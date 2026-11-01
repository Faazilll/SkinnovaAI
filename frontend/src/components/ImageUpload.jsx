import { useEffect, useRef, useState } from 'react'
import {
  AlertCircle,
  Camera,
  Check,
  CheckCircle2,
  Crosshair,
  FileImage,
  Layers,
  Microscope,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  SwitchCamera,
  Upload,
  Video,
  VideoOff,
  X,
  Zap,
} from 'lucide-react'
import { predictImage } from '../api'

const SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/webp']
const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024 // 15 MB

export default function ImageUpload({
  file,
  preview,
  onChange,
  allowCloseUp = true,
  onToggleAllowCloseUp,
  isScanning = false,
}) {
  const fileInputRef = useRef(null)
  const videoRef = useRef(null)
  const streamRef = useRef(null)

  const [inputMode, setInputMode] = useState('upload') // 'upload' | 'camera'
  const [cameraState, setCameraState] = useState('idle') // 'idle' | 'starting' | 'streaming' | 'captured' | 'error'
  const [cameraError, setCameraError] = useState('')
  const [capturedBlobUrl, setCapturedBlobUrl] = useState(null)
  const [capturedFile, setCapturedFile] = useState(null)
  const [facingMode, setFacingMode] = useState('user') // 'user' | 'environment'

  const [validationError, setValidationError] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [loadingSample, setLoadingSample] = useState(false)

  // Standalone image preview prediction state
  const [quickInspectLoading, setQuickInspectLoading] = useState(false)
  const [quickInspectResult, setQuickInspectResult] = useState(null)
  const [quickInspectError, setQuickInspectError] = useState('')

  // Cleanup camera stream on unmount or mode switch
  useEffect(() => {
    return () => {
      stopCameraStream()
    }
  }, [])

  useEffect(() => {
    // If preview changes externally or cleared, reset quick inspection
    if (!file) {
      setQuickInspectResult(null)
      setQuickInspectError('')
    }
  }, [file])

  function stopCameraStream() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  // Camera start handler
  async function startCamera(requestedFacing = facingMode) {
    stopCameraStream()
    setCameraError('')
    setCameraState('starting')

    if (!navigator?.mediaDevices?.getUserMedia) {
      setCameraError('Camera access is not supported by your current browser or connection.')
      setCameraState('error')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: requestedFacing,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      })

      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }
      setCameraState('streaming')
    } catch (err) {
      console.warn('Camera stream error:', err)
      let msg = 'Could not access camera device.'
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Camera permission denied. Please allow camera access in your browser settings to take a photo.'
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        msg = 'No camera hardware found on this system. Please connect a camera or use file upload.'
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        msg = 'Camera hardware is busy or in use by another application.'
      }
      setCameraError(msg)
      setCameraState('error')
    }
  }

  function handleSwitchInputMode(newMode) {
    if (newMode === inputMode) return
    setValidationError('')
    setCameraError('')
    if (newMode === 'camera') {
      setInputMode('camera')
      startCamera(facingMode)
    } else {
      stopCameraStream()
      setInputMode('upload')
      setCameraState('idle')
      if (capturedBlobUrl) {
        URL.revokeObjectURL(capturedBlobUrl)
        setCapturedBlobUrl(null)
        setCapturedFile(null)
      }
    }
  }

  // Toggle between front / back camera
  function toggleFacingMode() {
    const nextFacing = facingMode === 'user' ? 'environment' : 'user'
    setFacingMode(nextFacing)
    if (cameraState === 'streaming') {
      startCamera(nextFacing)
    }
  }

  // Capture frame from video stream
  function handleCapturePhoto() {
    if (!videoRef.current) return
    const video = videoRef.current
    const w = video.videoWidth || 1280
    const h = video.videoHeight || 720

    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d')

    // If front camera, mirror horizontally for natural feel
    if (facingMode === 'user') {
      ctx.translate(w, 0)
      ctx.scale(-1, 1)
    }
    ctx.drawImage(video, 0, 0, w, h)

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setCameraError('Failed to capture photo frame.')
          return
        }
        stopCameraStream()
        const photoFile = new File([blob], `camera_scan_${Date.now()}.jpg`, {
          type: 'image/jpeg',
        })
        const blobUrl = URL.createObjectURL(blob)
        setCapturedFile(photoFile)
        setCapturedBlobUrl(blobUrl)
        setCameraState('captured')
      },
      'image/jpeg',
      0.95
    )
  }

  // Confirm captured photo for analysis
  function handleAcceptCapturedPhoto() {
    if (!capturedFile) return
    setValidationError('')
    onChange(capturedFile)
    setInputMode('upload')
    setCameraState('idle')
    if (capturedBlobUrl) {
      URL.revokeObjectURL(capturedBlobUrl)
      setCapturedBlobUrl(null)
      setCapturedFile(null)
    }
  }

  // Retake photo
  function handleRetakePhoto() {
    if (capturedBlobUrl) {
      URL.revokeObjectURL(capturedBlobUrl)
      setCapturedBlobUrl(null)
      setCapturedFile(null)
    }
    startCamera(facingMode)
  }

  // Cancel camera capture
  function handleCancelCamera() {
    stopCameraStream()
    if (capturedBlobUrl) {
      URL.revokeObjectURL(capturedBlobUrl)
      setCapturedBlobUrl(null)
      setCapturedFile(null)
    }
    setCameraState('idle')
    setInputMode('upload')
  }

  // Validate file
  function validateFile(f) {
    if (!f) return 'No file selected.'
    if (f.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(f.size / (1024 * 1024)).toFixed(1)} MB) exceeds 15 MB limit. Please select a smaller photo.`
    }
    if (f.size <= 0) {
      return 'Selected file is empty (0 bytes).'
    }
    if (!f.type.startsWith('image/') && !SUPPORTED_FORMATS.includes(f.type.toLowerCase())) {
      return 'Unsupported file format. Please upload a JPEG, PNG, or WebP photo.'
    }
    return null
  }

  function handleFiles(files) {
    const f = files?.[0]
    if (!f) return
    const errorMsg = validateFile(f)
    if (errorMsg) {
      setValidationError(errorMsg)
      return
    }
    setValidationError('')
    setQuickInspectResult(null)
    setQuickInspectError('')
    onChange(f)
  }

  function handleClear(e) {
    e.stopPropagation()
    onChange(null)
    setValidationError('')
    setQuickInspectResult(null)
    setQuickInspectError('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // Load sample image directly from public folder
  async function loadSampleImage(samplePath, filename) {
    try {
      setLoadingSample(true)
      setValidationError('')
      setQuickInspectResult(null)
      setQuickInspectError('')
      const res = await fetch(samplePath)
      const blob = await res.blob()
      const sampleFile = new File([blob], filename, { type: 'image/jpeg' })
      onChange(sampleFile)
    } catch (err) {
      setValidationError('Failed to load sample image: ' + err.message)
    } finally {
      setLoadingSample(false)
    }
  }

  // Standalone inspection of the facial image using MobileNetV2
  async function handleQuickInspect() {
    if (!file) return
    setQuickInspectLoading(true)
    setQuickInspectError('')
    try {
      const res = await predictImage(file, true)
      setQuickInspectResult(res)
    } catch (err) {
      setQuickInspectError(err.message || 'Image prediction failed')
    } finally {
      setQuickInspectLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Input Mode Selector: Upload vs Camera */}
      <div className="grid grid-cols-2 gap-2 p-1 rounded-xl bg-slate-100 border border-slate-200">
        <button
          type="button"
          onClick={() => handleSwitchInputMode('upload')}
          className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-sans font-semibold transition cursor-pointer ${
            inputMode === 'upload'
              ? 'bg-white text-teal-800 shadow-sm border border-slate-200/80 font-bold'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Upload className="h-3.5 w-3.5" />
          <span>Upload Image</span>
        </button>

        <button
          type="button"
          onClick={() => handleSwitchInputMode('camera')}
          className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-sans font-semibold transition cursor-pointer ${
            inputMode === 'camera'
              ? 'bg-white text-teal-800 shadow-sm border border-slate-200/80 font-bold'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Camera className="h-3.5 w-3.5" />
          <span>Capture with Camera</span>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-500 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-600" />
          </span>
        </button>
      </div>

      {/* Validation Error Banner */}
      {validationError && (
        <div className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-800">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
          <div>
            <span className="font-semibold font-mono">Image Validation Error: </span>
            <span>{validationError}</span>
          </div>
        </div>
      )}

      {/* Mode A: Live Camera Workflow */}
      {inputMode === 'camera' && (
        <div className="space-y-3">
          {cameraError ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-6 text-center space-y-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
                <VideoOff className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h4 className="font-sans text-sm font-bold text-slate-900">Camera Access Required</h4>
                <p className="text-xs text-slate-600 max-w-sm mx-auto leading-relaxed">
                  {cameraError}
                </p>
              </div>
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => startCamera(facingMode)}
                  className="flex items-center gap-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 px-3.5 py-2 text-xs font-sans font-medium text-slate-700 transition"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>Retry Camera</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleSwitchInputMode('upload')}
                  className="flex items-center gap-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 px-3.5 py-2 text-xs font-sans font-medium text-white transition shadow-sm"
                >
                  <Upload className="h-3.5 w-3.5" />
                  <span>Switch to Upload</span>
                </button>
              </div>
            </div>
          ) : cameraState === 'captured' ? (
            /* Review Captured Snapshot */
            <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-4 space-y-3 shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200 text-xs">
                <span className="text-teal-800 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-teal-700" />
                  <span>Photo Captured — Review Frame</span>
                </span>
                <span className="text-slate-500 font-mono">
                  {capturedFile ? `${Math.round(capturedFile.size / 1024)} KB` : ''}
                </span>
              </div>

              <div className="relative flex justify-center bg-slate-900 rounded-xl overflow-hidden max-h-[340px]">
                {capturedBlobUrl && (
                  <img
                    src={capturedBlobUrl}
                    alt="Captured dermatological scan"
                    className="object-contain max-h-[340px] rounded-lg"
                  />
                )}
              </div>

              {/* Review Controls */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleRetakePhoto}
                    className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 px-3.5 py-2 text-xs font-sans font-medium text-slate-700 transition"
                  >
                    <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
                    <span>Retake Photo</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelCamera}
                    className="flex items-center gap-1.5 rounded-xl border border-slate-200 hover:bg-slate-100 px-3 py-2 text-xs font-sans text-slate-600 transition"
                  >
                    <X className="h-3.5 w-3.5" />
                    <span>Cancel</span>
                  </button>
                </div>

                <button
                  type="button"
                  onClick={handleAcceptCapturedPhoto}
                  className="flex items-center gap-2 rounded-xl bg-teal-700 hover:bg-teal-800 px-4 py-2 text-xs font-sans font-bold text-white shadow-sm transition"
                >
                  <Check className="h-4 w-4" />
                  <span>Accept Photograph</span>
                </button>
              </div>
            </div>
          ) : (
            /* Live Camera Stream Viewfinder */
            <div className="relative overflow-hidden rounded-2xl border border-slate-300 bg-slate-950 shadow-md">
              <div className="relative aspect-video max-h-[360px] w-full bg-slate-950 flex items-center justify-center overflow-hidden">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`w-full h-full object-cover ${
                    facingMode === 'user' ? 'scale-x-[-1]' : ''
                  }`}
                />

                {/* Clinical Viewfinder Overlay */}
                <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-3.5">
                  <div className="flex items-center justify-between text-[10px] font-mono text-teal-300 bg-slate-900/80 rounded px-2.5 py-1 backdrop-blur-sm self-start">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      <span>CLINICAL PHOTOGRAPHY VIEWFINDER</span>
                    </span>
                  </div>

                  {/* Centered Face Framing Guide */}
                  <div className="self-center flex flex-col items-center justify-center my-auto">
                    <div className="w-44 h-56 border-2 border-dashed border-teal-400/70 rounded-[90px] flex items-center justify-center">
                      <Crosshair className="h-7 w-7 text-teal-300/50" />
                    </div>
                    <span className="text-[10px] font-mono text-white mt-2 bg-slate-900/80 px-2 py-0.5 rounded backdrop-blur-sm">
                      [ POSITION FACE IN OVAL ]
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-300 bg-slate-900/60 px-2 py-0.5 rounded">
                    <span>YUNET FACE DETECTION</span>
                    <span>HAYASHI SCALE 0–3</span>
                  </div>
                </div>

                {/* Loading state indicator */}
                {cameraState === 'starting' && (
                  <div className="absolute inset-0 bg-slate-900/90 flex flex-col items-center justify-center gap-2.5 text-xs font-sans text-teal-300">
                    <span className="h-6 w-6 border-2 border-teal-400 border-t-transparent rounded-full animate-spin" />
                    <span>Initializing camera stream…</span>
                  </div>
                )}
              </div>

              {/* Viewfinder Bottom Toolbar */}
              <div className="flex items-center justify-between p-3 bg-slate-900 border-t border-slate-800">
                <button
                  type="button"
                  onClick={toggleFacingMode}
                  title="Switch camera facing mode"
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-2 text-xs font-sans text-slate-200 transition"
                >
                  <SwitchCamera className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Flip Camera</span>
                </button>

                <button
                  type="button"
                  onClick={handleCapturePhoto}
                  disabled={cameraState !== 'streaming'}
                  className="flex items-center gap-2 rounded-xl bg-teal-600 hover:bg-teal-500 px-5 py-2.5 text-xs font-sans font-bold text-white shadow-sm transition disabled:opacity-50"
                >
                  <Camera className="h-4 w-4" />
                  <span>Capture Photo</span>
                </button>

                <button
                  type="button"
                  onClick={handleCancelCamera}
                  className="flex items-center gap-1.5 rounded-lg border border-slate-700 hover:bg-slate-800 px-3 py-2 text-xs font-sans text-slate-300 transition"
                >
                  <X className="h-3.5 w-3.5" />
                  <span>Cancel</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Mode B: Preserved File Upload Dropzone */}
      {inputMode === 'upload' && (
        <div className="space-y-3">
          {/* Clinical Benchmark Preset Bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
              <Zap className="h-3.5 w-3.5 text-teal-700" />
              <span>Standard Clinical Test Image:</span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                disabled={loadingSample}
                onClick={() => loadSampleImage('/sample_face.jpg', 'clinical_face_portrait.jpg')}
                className="flex items-center gap-1.5 rounded-lg border border-teal-200 bg-teal-50 hover:bg-teal-100 px-3 py-1 text-xs font-sans font-semibold text-teal-800 transition cursor-pointer"
              >
                <span>Frontal Facial Portrait (Grade 1)</span>
              </button>
              <button
                type="button"
                disabled={loadingSample}
                onClick={() => loadSampleImage('/sample_lesion.jpg', 'clinical_lesion_closeup.jpg')}
                className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 hover:bg-amber-100 px-3 py-1 text-xs font-sans font-semibold text-amber-800 transition cursor-pointer"
              >
                <span>Close-up Lesion (Grade 2/3)</span>
              </button>
            </div>

          </div>

          {/* Main Upload Dropzone */}
          <div
            className={`relative overflow-hidden rounded-2xl border-2 transition-all duration-200 ${
              dragActive
                ? 'border-teal-600 bg-teal-50/50'
                : 'border-dashed border-slate-300 hover:border-teal-600 bg-slate-50/70 hover:bg-slate-50'
            }`}
            onDragOver={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragActive(false)
              handleFiles(e.dataTransfer.files)
            }}
          >
            <button
              type="button"
              className="flex w-full min-h-[240px] flex-col items-center justify-center p-6 text-center outline-none cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              {preview ? (
                <div className="relative group max-w-full">
                  <div className="relative overflow-hidden rounded-xl border border-slate-300 shadow-sm bg-white">
                    <img
                      src={preview}
                      alt="Clinical scan input"
                      className="max-h-64 object-contain rounded-lg"
                    />

                    {/* Clean Clinical Grid Framing Overlay */}
                    <div className="absolute inset-0 pointer-events-none">
                      <div className="scanning-laser" />
                      <div className="absolute inset-2 border border-teal-700/20 rounded-md pointer-events-none flex flex-col justify-between p-2">
                        <div className="flex justify-between items-center text-[10px] font-mono text-teal-800 bg-white/80 px-1.5 py-0.5 rounded">
                          <span>YUNET 224x224 MATRIX</span>
                          <span>SKIN VERIFIED</span>
                        </div>
                        <div className="flex justify-between items-center text-[10px] font-mono text-slate-700 bg-white/80 px-1.5 py-0.5 rounded self-end">
                          <span>HAYASHI 0–3</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Remove button */}
                  <button
                    type="button"
                    onClick={handleClear}
                    title="Remove image"
                    className="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-white/90 border border-slate-300 text-slate-700 hover:text-white hover:bg-rose-600 transition shadow-sm"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2.5">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 border border-teal-200 text-teal-700">
                    <Upload className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-sans text-sm font-bold text-slate-900">
                      Upload Frontal Facial Skin Photograph
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500 max-w-sm">
                      Drag & drop or browse file · Accepts JPEG, PNG, or WebP (up to 15 MB)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-[11px] font-sans text-slate-600">
                      Standard Frontal Framing
                    </span>
                    <span className="rounded-full bg-teal-50 border border-teal-200 px-2.5 py-0.5 text-[11px] font-sans font-medium text-teal-800">
                      Automatic YuNet Face Alignment
                    </span>
                  </div>
                </div>
              )}

              {file && (
                <div className="mt-3 flex items-center gap-2 rounded-lg bg-white border border-slate-200 px-3 py-1.5 text-xs font-sans text-slate-700 shadow-sm">
                  <FileImage className="h-4 w-4 text-teal-700" />
                  <span className="font-medium truncate max-w-[200px]">{file.name}</span>
                  <span className="text-slate-400 font-mono">({Math.round(file.size / 1024)} KB)</span>
                </div>
              )}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>
        </div>
      )}

      {/* Standalone Visual AI Quick Inspection Panel */}
      {file && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Microscope className="h-4 w-4 text-teal-700" />
              <span className="text-xs font-sans font-bold text-slate-900">
                Visual Deep Learning Model Quick-Inspect
              </span>
            </div>
            <button
              type="button"
              disabled={quickInspectLoading}
              onClick={handleQuickInspect}
              className="flex items-center gap-1.5 rounded-lg border border-teal-200 bg-white hover:bg-teal-50 px-2.5 py-1 text-xs font-sans font-semibold text-teal-800 transition shadow-sm cursor-pointer"
            >
              {quickInspectLoading ? (
                <>
                  <span className="h-3 w-3 border-2 border-teal-700 border-t-transparent rounded-full animate-spin" />
                  <span>Evaluating CNN…</span>
                </>
              ) : (
                <>
                  <Zap className="h-3 w-3 text-teal-700" />
                  <span>Inspect Visual AI Prediction</span>
                </>
              )}
            </button>
          </div>

          {quickInspectError && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-800 font-sans">
              {quickInspectError}
            </div>
          )}

          {quickInspectResult && (
            <div className="rounded-lg bg-white border border-slate-200 p-3 text-xs font-mono space-y-1.5 shadow-sm">
              <div className="flex justify-between items-center pb-1.5 border-b border-slate-200">
                <span className="text-slate-500 font-sans">Hayashi Classification:</span>
                <span className="text-teal-800 font-bold">
                  Grade {quickInspectResult.severity}: {quickInspectResult.severity_label}
                </span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-500 font-sans">Class Probabilities:</span>
                <span className="text-slate-700">
                  G0: {Math.round(quickInspectResult.class_probabilities?.['0'] * 100)}% | G1:{' '}
                  {Math.round(quickInspectResult.class_probabilities?.['1'] * 100)}% | G2:{' '}
                  {Math.round(quickInspectResult.class_probabilities?.['2'] * 100)}% | G3:{' '}
                  {Math.round(quickInspectResult.class_probabilities?.['3'] * 100)}%
                </span>
              </div>
              <div className="flex justify-between items-center text-[11px]">
                <span className="text-slate-500 font-sans">Face Detected:</span>
                <span
                  className={
                    quickInspectResult.face_detected ? 'text-emerald-700 font-bold' : 'text-amber-700 font-bold'
                  }
                >
                  {quickInspectResult.face_detected ? 'Yes (YuNet)' : 'Regional Fallback'}
                </span>
              </div>
              <div className="flex justify-between items-center pt-1 border-t border-slate-200 text-[11px]">
                <span className="text-slate-500 font-sans">Active Architecture:</span>
                <span className="text-slate-700">{quickInspectResult.method}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Strict Facial Skin Biometric Protocol Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl bg-slate-50 border border-slate-200 px-4 py-3 text-xs shadow-sm">
        <div className="flex items-center gap-2.5 text-slate-700">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-teal-100 text-teal-800 border border-teal-200">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <div className="font-bold font-sans text-slate-900 text-xs flex items-center gap-2">
              <span>Facial Skin Quality Protocol</span>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            </div>
            <p className="text-[11px] text-slate-500 font-sans">
              YuNet 224x224 Biometric Aligner · Non-facial skin images flagged for clinician review
            </p>
          </div>
        </div>
        <span className="rounded-full px-2.5 py-0.5 text-[10px] font-sans font-bold uppercase tracking-wider border text-emerald-800 bg-emerald-50 border-emerald-200 flex items-center gap-1 self-start sm:self-center">
          <Check className="h-3 w-3" />
          <span>Validated Standard</span>
        </span>
      </div>
    </div>
  )
}

