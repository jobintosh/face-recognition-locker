console.log(recognizeURL);

const videoElement = document.getElementById('camera-stream');
var mediaStream;

// Function to start the camera and return a promise
const startCamera = () => {
    return new Promise(async (resolve, reject) => {
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = mediaStream;
            resolve('Camera started');
        } catch (error) {
            reject(error);
        }
    });
};

// Function to stop the camera
const stopCamera = () => {
    if (mediaStream) {
        mediaStream.getTracks().forEach((track) => track.stop());
        videoElement.srcObject = null;
    }
};

function updateImageOutput(data) {
    const imageContainer = document.getElementById('imageContainer');

    // Create an image element
    const imgElement = document.createElement('img');
    imgElement.style = "max-width: 500px; max-height: 500px;";
    imgElement.src = 'data:image/jpeg;base64,' + data.image64;

    // Create a paragraph element for the label
    // const labelElement = document.createElement('p');
    // labelElement.textContent = 'Label: ' + data.label;
    //labelElement.textContent = 'confidence: ' + result.confidence;

    // Clear the loading message and append the image and label
    imageContainer.innerHTML = '';
    imageContainer.appendChild(imgElement);
    imageContainer.appendChild(labelElement);
}

function captureFrame() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;

    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg').split(',')[1]; // Convert to base64 image data

    fetch(recognizeURL, {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: { 'Content-Type': 'application/json' }
    })
        .then(response => response.json())
        .then(data => {
            if (!data || !data.image64) return;

            if (data.message === 'done') {
                updateImageOutput(data);
            }

            if (data.message) console.log(data.message);
        })
        .catch(error => {
            console.error('Fetch error: ');
            console.error(error);
        });
}

// Start capturing frames when the video is playing
videoElement.addEventListener('play', function () {
    setInterval(captureFrame, 3000); // Capture frame every 1 second
});

// Optionally, you can stop capturing frames when the video is paused or ended
videoElement.addEventListener('pause', function () {
    clearInterval(captureFrame);
});
videoElement.addEventListener('ended', function () {
    clearInterval(captureFrame);
});

startCamera();
