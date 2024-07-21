---

# Face Recognition Locker System

## Overview

This project is a final-year university project developed using Python, OpenCV, and Flask. It provides a comprehensive locker management system that utilizes face recognition technology to control electric solenoid locks. The system also integrates subscription management, notifications, and logging functionalities.

## Features

1. **User Management**
   - Register and login users
   - Password recovery
   - Update user information

2. **Subscription Management**
   - Integration with Stripe for managing access to the Face Recognition system

3. **Notifications**
   - Line notifications for:
     - Locker status (which locker is opened, by which user, and at what time)
     - Alerts if a door remains open beyond a specified time

4. **Logging**
   - Detailed logs of user actions and system events

5. **API Integration**
   - Operates through an API endpoint (`/loaddata`)
   - Controls two ESP8266 boards to manage solenoid locks and check signals from reed sensors

## Installation

### Prerequisites

- Docker
- Docker Compose
- Stripe API key
- ESP8266 boards

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jobintosh/face-recognition-locker.git
   ```

2. **Navigate to the project directory:**
   ```bash
   cd face-recognition-locker
   ```

3. **Build and run the Docker containers:**
   ```bash
   docker-compose up --build
   ```

4. **Access the system via:**
   - Web Interface: `http://127.0.0.1`
   - API Endpoint: `http://127.0.0.1/loaddata`
   - Online Demo: [locker.jobintosh.me](http://locker.jobintosh.me)

## Usage

1. **User Registration and Login:**
   - Access the registration and login pages via the web interface.
   - For demo purposes, use the following credentials to log in:
     - **Username:** `jobintosh`
     - **Password:** `jobintosh`
   - Follow the instructions to create an account and log in.

2. **Subscription Management:**
   - Subscribe or manage your subscription via the Stripe integration.

3. **Notifications:**
   - Configure Line notifications to receive alerts about locker status and events.

4. **Monitoring and Logs:**
   - Check the logs to review system activities and user actions.

## Contributing

Feel free to fork this repository and submit pull requests with improvements or bug fixes. For any issues or feature requests, please open an issue in the GitHub repository.

## Acknowledgements

- [OpenCV](https://opencv.org/) for computer vision functionalities.
- [Flask](https://flask.palletsprojects.com/) for the web framework.
- [Stripe](https://stripe.com/) for subscription management.
- [ESP8266](https://www.esp8266.com/) for hardware interfacing.

## Disclaimer

This project is for educational purposes and may require additional security measures before deploying in a production environment.

## Contact

For any questions or feedback, please reach out to [tharathorn.chongsaeng@gmail.com]

---

**For fellow students:** If you find this project useful, feel free to clone and build upon it for your own projects. Good luck with your studies and projects!

---
## Demo Video
- [Watch the demo video on YouTube](https://youtu.be/uIi0rAEMXK0)

![IMG_0209](https://github.com/user-attachments/assets/c087984a-dd37-426e-ab39-277f1f2fad96)
![IMG_0152](https://github.com/user-attachments/assets/cd9572db-314e-4025-8f83-e287359ab393)

---
