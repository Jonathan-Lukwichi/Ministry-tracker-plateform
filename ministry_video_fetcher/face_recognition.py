"""
Face Recognition Module for Ministry Video Fetcher

Enhanced face recognition with video frame extraction and
multi-frame analysis for accurate preacher identification.
"""

import os
import glob
import tempfile
import shutil
from typing import List, Tuple, Optional
from dataclasses import dataclass
import requests
import io
import numpy as np
from PIL import Image
import cv2

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Warning: DeepFace not available (requires TensorFlow, which needs Python 3.11 or 3.12).")
    print("         Using OpenCV-based face detection as fallback (detection only, no recognition).")

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("Warning: yt-dlp not available. Frame extraction disabled.")


@dataclass
class FaceResult:
    """Result of face verification."""
    verified: bool
    confidence: float
    source: str  # 'thumbnail', 'frame_1', 'frame_2', etc.
    distance: float = 0.0
    model_used: str = ""
    error: Optional[str] = None


class FaceRecognizer:
    """
    Enhanced face recognition with video frame extraction.

    Features:
    - Thumbnail-first approach (fast path)
    - Video frame extraction for deeper analysis
    - Multiple detector backends for reliability
    - Configurable thresholds
    """

    # Default configuration
    DEFAULT_CONFIG = {
        "model_name": "VGG-Face",  # Options: VGG-Face, Facenet, Facenet512, ArcFace, OpenFace, DeepFace, DeepID, Dlib, SFace
        "detector_backend": "opencv",  # Options: opencv, ssd, dlib, mtcnn, retinaface, mediapipe
        "distance_metric": "cosine",  # Options: cosine, euclidean, euclidean_l2
        "distance_threshold": 0.40,  # Lower = stricter matching
        "num_frames": 5,
        "frame_interval_seconds": 10,
        "enable_frame_extraction": True,
        "video_segment_duration": 60,  # Download first 60 seconds
    }

    def __init__(self, config: dict = None, photos_dir: str = "photos"):
        """
        Initialize face recognizer.

        Args:
            config: Optional configuration override
            photos_dir: Directory containing reference photos
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.photos_dir = photos_dir
        self.reference_image_paths = []
        self.model_loaded = False

        self._load_reference_images()
        self._initialize_model()

    def _load_reference_images(self):
        """Load reference images from the photos directory."""
        if not os.path.isdir(self.photos_dir):
            print(f"Warning: Photos directory '{self.photos_dir}' not found.")
            return

        supported_formats = ('*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG')
        for fmt in supported_formats:
            self.reference_image_paths.extend(
                glob.glob(os.path.join(self.photos_dir, fmt))
            )

        if self.reference_image_paths:
            print(f"Loaded {len(self.reference_image_paths)} reference images.")
        else:
            print(f"Warning: No reference images found in '{self.photos_dir}'.")

    def _initialize_model(self):
        """Pre-load the face recognition model."""
        # Load OpenCV cascade for fallback face detection
        self.face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                self.face_cascade = None
        except Exception:
            pass

        if not DEEPFACE_AVAILABLE or not self.reference_image_paths:
            if self.face_cascade is not None:
                self.model_loaded = True
                print("OpenCV face detection (fallback mode) loaded successfully.")
            return

        try:
            # Build the model once to avoid repeated initialization
            DeepFace.build_model(self.config["model_name"])
            self.model_loaded = True
            print(f"Face recognition model '{self.config['model_name']}' loaded successfully.")
        except Exception as e:
            print(f"Warning: Could not load face recognition model: {e}")
            # Still mark as loaded if OpenCV fallback is available
            if self.face_cascade is not None:
                self.model_loaded = True
                print("Falling back to OpenCV face detection.")
            else:
                self.model_loaded = False

    def verify_face(self, video_url: str, thumbnail_url: str = None,
                    use_frames: bool = True) -> FaceResult:
        """
        Verify if the target person's face appears in a video.

        Args:
            video_url: URL of the video
            thumbnail_url: URL of the video thumbnail (optional)
            use_frames: Whether to extract video frames if thumbnail fails

        Returns:
            FaceResult with verification status
        """
        # Use OpenCV fallback if DeepFace not available
        if not DEEPFACE_AVAILABLE:
            if self.face_cascade is not None:
                return self._verify_with_opencv_fallback(video_url, thumbnail_url, use_frames)
            return FaceResult(
                verified=False,
                confidence=0.0,
                source="none",
                error="Face recognition not available (install TensorFlow with Python 3.11/3.12)"
            )

        if not self.reference_image_paths:
            return FaceResult(
                verified=False,
                confidence=0.0,
                source="none",
                error="No reference photos uploaded"
            )

        # Step 1: Try thumbnail first (fast path)
        if thumbnail_url:
            result = self._verify_thumbnail(thumbnail_url)
            if result.verified:
                return result

        # Step 2: Extract and check video frames if enabled
        if use_frames and self.config["enable_frame_extraction"] and video_url:
            result = self._verify_video_frames(video_url)
            if result.verified:
                return result

        # No face found
        return FaceResult(
            verified=False,
            confidence=0.0,
            source="none",
            error="Face not found in thumbnail or video frames"
        )

    def _verify_thumbnail(self, thumbnail_url: str) -> FaceResult:
        """Verify face in video thumbnail."""
        try:
            # Download thumbnail
            response = requests.get(thumbnail_url, timeout=15)
            response.raise_for_status()

            # Convert to numpy array
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            image_np = np.array(image)

            # Compare against reference images
            verified, confidence, distance = self._compare_against_references(image_np)

            return FaceResult(
                verified=verified,
                confidence=confidence,
                source="thumbnail",
                distance=distance,
                model_used=self.config["model_name"]
            )

        except requests.exceptions.RequestException as e:
            return FaceResult(
                verified=False,
                confidence=0.0,
                source="thumbnail",
                error=f"Failed to download thumbnail: {e}"
            )
        except Exception as e:
            return FaceResult(
                verified=False,
                confidence=0.0,
                source="thumbnail",
                error=f"Thumbnail verification error: {e}"
            )

    def _verify_video_frames(self, video_url: str) -> FaceResult:
        """Extract frames from video and verify faces."""
        if not YTDLP_AVAILABLE:
            return FaceResult(
                verified=False,
                confidence=0.0,
                source="frames",
                error="yt-dlp not available for frame extraction"
            )

        frames = self._extract_frames(video_url)
        if not frames:
            return FaceResult(
                verified=False,
                confidence=0.0,
                source="frames",
                error="Could not extract frames from video"
            )

        # Check each frame
        for i, frame in enumerate(frames):
            verified, confidence, distance = self._compare_against_references(frame)
            if verified:
                return FaceResult(
                    verified=True,
                    confidence=confidence,
                    source=f"frame_{i+1}",
                    distance=distance,
                    model_used=self.config["model_name"]
                )

        return FaceResult(
            verified=False,
            confidence=0.0,
            source="frames",
            error=f"Face not found in {len(frames)} extracted frames"
        )

    def _extract_frames(self, video_url: str) -> List[np.ndarray]:
        """
        Extract frames from a video URL.

        Downloads a short segment of the video and extracts evenly-spaced frames.
        """
        frames = []
        temp_dir = None

        try:
            # Create temporary directory for video download
            temp_dir = tempfile.mkdtemp(prefix="ministry_face_")
            video_path = os.path.join(temp_dir, "video.mp4")

            # Configure yt-dlp to download only first segment
            ydl_opts = {
                'format': 'worst[ext=mp4]/worst',  # Smallest format for speed
                'outtmpl': video_path,
                'quiet': True,
                'no_warnings': True,
                'download_ranges': lambda info, ydl: [
                    {'start_time': 0, 'end_time': self.config["video_segment_duration"]}
                ],
                'force_keyframes_at_cuts': True,
            }

            # Download video segment
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            if not os.path.exists(video_path):
                print(f"Warning: Video file not created for {video_url}")
                return frames

            # Open video with OpenCV
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Warning: Could not open video {video_url}")
                return frames

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Calculate frame positions to extract
            num_frames = min(self.config["num_frames"], max(1, total_frames // int(fps)))
            frame_interval = max(1, total_frames // (num_frames + 1))

            for i in range(num_frames):
                frame_pos = (i + 1) * frame_interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)

            cap.release()
            print(f"Extracted {len(frames)} frames from video.")

        except Exception as e:
            print(f"Warning: Frame extraction failed for {video_url}: {e}")

        finally:
            # Cleanup temporary files
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

        return frames

    def _compare_against_references(self, image: np.ndarray) -> Tuple[bool, float, float]:
        """
        Compare an image against all reference images.

        Args:
            image: NumPy array of the image to check (RGB format)

        Returns:
            Tuple of (verified, confidence, distance)
        """
        best_distance = float('inf')
        verified = False

        for ref_path in self.reference_image_paths:
            try:
                result = DeepFace.verify(
                    img1_path=image,
                    img2_path=ref_path,
                    model_name=self.config["model_name"],
                    detector_backend=self.config["detector_backend"],
                    distance_metric=self.config["distance_metric"],
                    enforce_detection=False,  # Don't fail if no face detected
                )

                distance = result.get("distance", 1.0)
                if distance < best_distance:
                    best_distance = distance

                if result.get("verified", False):
                    # Calculate confidence from distance
                    confidence = max(0, 1 - distance) * 0.98
                    return True, confidence, distance

            except Exception as e:
                # Continue to next reference image if one fails
                continue

        # No match found - return best distance anyway
        confidence = max(0, 1 - best_distance) * 0.5  # Lower confidence for non-match
        return False, confidence, best_distance

    def _verify_with_opencv_fallback(self, video_url: str, thumbnail_url: str = None,
                                      use_frames: bool = True) -> FaceResult:
        """
        Fallback face detection using OpenCV Haar Cascades.

        IMPORTANT: This only detects if faces are present, NOT if they match reference photos.
        Therefore it should NEVER return verified=True, only indicate face_detected.

        Used when DeepFace/TensorFlow is not available.
        """
        face_detected = False
        source = "opencv_fallback"

        # Try thumbnail first
        if thumbnail_url:
            try:
                response = requests.get(thumbnail_url, timeout=15)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                image_np = np.array(image)

                if self._detect_face_opencv(image_np):
                    face_detected = True
                    source = "thumbnail (opencv)"
            except Exception:
                pass

        # Try video frames if thumbnail failed
        if not face_detected and use_frames and video_url:
            frames = self._extract_frames(video_url)
            for i, frame in enumerate(frames):
                if self._detect_face_opencv(frame):
                    face_detected = True
                    source = f"frame_{i+1} (opencv)"
                    break

        if face_detected:
            # CRITICAL: Return verified=False with low confidence
            # OpenCV can only detect faces, NOT verify identity
            return FaceResult(
                verified=False,  # CHANGED from True - cannot verify without reference comparison
                confidence=0.20,  # CHANGED from 0.50 - very low confidence for detection only
                source=source,
                distance=0.8,
                model_used="OpenCV Haar Cascade (detection only)",
                error="Face detected but NOT verified - DeepFace required for identity verification"
            )

        return FaceResult(
            verified=False,
            confidence=0.0,
            source="opencv_fallback",
            error="No faces detected in thumbnail or video frames"
        )

    def _detect_face_opencv(self, image: np.ndarray) -> bool:
        """Detect if a face is present using OpenCV Haar Cascades."""
        if self.face_cascade is None:
            return False

        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            return len(faces) > 0
        except Exception:
            return False

    def get_reference_photos(self) -> List[dict]:
        """Get list of reference photos with metadata."""
        photos = []
        for path in self.reference_image_paths:
            filename = os.path.basename(path)
            try:
                size = os.path.getsize(path)
                photos.append({
                    "filename": filename,
                    "path": path,
                    "size": size,
                })
            except Exception:
                photos.append({
                    "filename": filename,
                    "path": path,
                    "size": 0,
                })
        return photos

    def add_reference_photo(self, filename: str, image_data: bytes) -> bool:
        """
        Add a new reference photo.

        Args:
            filename: Name for the new photo file
            image_data: Raw image bytes

        Returns:
            True if successful
        """
        try:
            # Ensure photos directory exists
            os.makedirs(self.photos_dir, exist_ok=True)

            # Save the image
            filepath = os.path.join(self.photos_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)

            # Reload reference images
            self._load_reference_images()
            return True

        except Exception as e:
            print(f"Error adding reference photo: {e}")
            return False

    def remove_reference_photo(self, filename: str) -> bool:
        """
        Remove a reference photo.

        Args:
            filename: Name of the photo to remove

        Returns:
            True if successful
        """
        try:
            filepath = os.path.join(self.photos_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                self._load_reference_images()
                return True
            return False

        except Exception as e:
            print(f"Error removing reference photo: {e}")
            return False

    def test_recognition(self, video_url: str) -> dict:
        """
        Test face recognition on a video URL.

        Returns detailed results for debugging.
        """
        result = self.verify_face(video_url, use_frames=True)
        return {
            "verified": result.verified,
            "confidence": result.confidence,
            "source": result.source,
            "distance": result.distance,
            "model": result.model_used,
            "error": result.error,
            "reference_photos": len(self.reference_image_paths),
        }


# Singleton instance for reuse
_recognizer_instance: Optional[FaceRecognizer] = None


def get_face_recognizer(config: dict = None, photos_dir: str = "photos") -> FaceRecognizer:
    """Get or create the face recognizer singleton."""
    global _recognizer_instance
    if _recognizer_instance is None:
        _recognizer_instance = FaceRecognizer(config, photos_dir)
    return _recognizer_instance


def verify_face_in_video(video_url: str, thumbnail_url: str = None,
                         use_frames: bool = True) -> FaceResult:
    """Convenience function to verify a face in a video."""
    recognizer = get_face_recognizer()
    return recognizer.verify_face(video_url, thumbnail_url, use_frames)
