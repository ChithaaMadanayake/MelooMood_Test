document.addEventListener("DOMContentLoaded", () => {
  const video        = document.getElementById("video");
  const circleVideo  = document.getElementById("circle-video");
  const circleSource = document.getElementById("circle-source");
  const canvas       = document.getElementById("canvas");
  const startBtn     = document.getElementById("startWebcam");
  const captureBtn   = document.getElementById("captureButton");
  const disp         = document.getElementById("emotion-display");
  const musicPlayer  = document.getElementById("music-player");
  const musicSource  = document.getElementById("music-source");
  const splashScreen = document.getElementById("splash-screen");
  const mainContent  = document.getElementById("main-content");

  let stream = null;

  // Splash screen
  setTimeout(() => {
    splashScreen.classList.add("fade-out");
    setTimeout(() => {
      splashScreen.style.display = "none";
      mainContent.style.display = "block";
      playRandomCircleVideo(); // Play random on page load
    }, 2000);
  }, 10000);
// Function to scroll to the main section
function scrollToMainSection() {
  const mainSection = document.getElementById("main-section");
  window.scrollTo({
    top: mainSection.offsetTop, 
    behavior: 'smooth'
  });
}
  // Play random circle video
  function playRandomCircleVideo() {
    const randomNum = Math.floor(Math.random() * 6) + 1; // 1 to 6
    const newPath = `/static/circle${randomNum}.mp4`;
    circleSource.src = newPath;
    circleVideo.load();
    circleVideo.play();
    circleVideo.style.display = "block";
    video.style.display = "none";
  }

  // Start webcam
  startBtn.addEventListener("click", async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      video.srcObject = stream;
      video.style.display = "block";
      circleVideo.pause();
      circleVideo.style.display = "none";
      captureBtn.style.display = "inline-block";
      startBtn.style.display = "none";
    } catch {
      alert("Webcam access denied.");
    }
  });

  // Capture and detect emotion
  captureBtn.addEventListener("click", async () => {
    // Stop any music
    musicPlayer.pause();
    musicPlayer.currentTime = 0;

    // Stop webcam before capture
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const imgData = canvas.toDataURL("image/png");

    // Turn off webcam
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }

    video.style.display = "none";
    disp.innerText = "Detecting emotion…";

    fetch("/detect-emotion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image: imgData })
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        disp.innerText = data.error;
        return;
      }

      disp.innerHTML = `<strong>${data.emotion}</strong><br>${data.message}`;

      // Play music
      if (data.music) {
        musicSource.src = data.music;
        musicPlayer.style.display = "block";
        musicPlayer.load();
        musicPlayer.play();
      }

      // After detection, show random video again
      setTimeout(() => {
        playRandomCircleVideo();
      }, 1000);
    })
    .catch(err => {
      console.error(err);
      disp.innerText = "Something went wrong.";
    });
  });

  // Optional: if music stops, still show random circle video
  musicPlayer.addEventListener("pause", () => {
    if (!video.srcObject) {
      playRandomCircleVideo();
    }
  });

  // Hide circle video when webcam is turned on
  startBtn.addEventListener("click", () => {
    circleVideo.style.display = "none";
    circleVideo.pause();
  });
});


