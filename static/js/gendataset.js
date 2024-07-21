
console.log("uploadURL", uploadURL);

const videoElement = document.getElementById('camera-stream');
var mediaStream;
var isDone = false;
var interval;

function updateResult(text, textColor) {
    // Get the <div> element by its id
    var resultDiv = document.getElementById('result');

    // Update the inner text of the <div>
    resultDiv.innerText = text;

    // Update the text color
    resultDiv.style.color = textColor;
}

function updateImageOutput(data) {
    const imageContainer = document.getElementById('imageContainer');

    // Create an image element
    const imgElement = document.createElement('img');
    imgElement.style = "max-width: 500px; max-height: 500px;";
    imgElement.src = 'data:image/jpeg;base64,' + data.image64;

    // Create a paragraph element for the label
    // const labelElement = document.createElement('p');
    // labelElement.textContent = 'Label: ' + data.label;

    // Clear the loading message and append the image and label
    imageContainer.innerHTML = '';
    imageContainer.appendChild(imgElement);
    // imageContainer.appendChild(labelElement);
}

// Function to start the camera and return a promise
const startCamera = () => {
    return new Promise(async (resolve, reject) => {
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ video: true })
            videoElement.srcObject = mediaStream
            resolve('Camera started')
        } catch (error) {
            reject(error)
        }
    })
}

// Function to stop the camera
const stopCamera = () => {
    if (mediaStream) {
        mediaStream.getTracks().forEach((track) => track.stop())
        videoElement.srcObject = null
    }
}


function captureFrame() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;

    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg').split(',')[1];; // Convert to base64 image data
    // console.log(imageData);

    fetch(uploadURL, {
        method: 'POST',
        body: JSON.stringify({ image: imageData }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then((response) => response.json())
        .then((data) => {
            console.log('Server response:')
            console.log(data)

            if (!data) return;

            if (data.status && data.status.includes("done") && isDone == false) {
                isDone = true;

                clearInterval(interval);
                // alert("Done! training model!");
                updateResult("Done! please wait for model training...", "green");

                window.location.replace(trainURL);
                return;
            }

            if (data.message.includes("successfully")) {
                updateResult(`Face detected! (only ${100 - data.image_count} left!)`, "green");

                updateImageOutput(data);
            } else if (data.message.includes("face not found")) {
                updateResult(`Face not found! please move a little bit!)`, "red");
            }
        })
        .catch((error) => {
            console.error('Error sending data to server:', error)
        })
}

// Start capturing frames when the video is playing
videoElement.addEventListener('play', function () {
    captureFrame();
});

// Optionally, you can stop capturing frames when the video is paused or ended
videoElement.addEventListener('pause', function () {
    cancelAnimationFrame(captureFrame);
});
videoElement.addEventListener('ended', function () {
    cancelAnimationFrame(captureFrame);
});

startCamera()

interval = setInterval(() => {
    captureFrame()
}, 100);
