// Initialize Firebase Authentication
const auth = firebase.auth();

// Function to handle login
function login() {
    const email = document.getElementById('username_or_email').value;
    const password = document.getElementById('password').value;

    auth.signInWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // Successfully logged in
            const user = userCredential.user;
            // Redirect or perform other actions after login
            console.log('Logged in as:', user.email);
        })
        .catch((error) => {
            // Handle login error
            const errorCode = error.code;
            const errorMessage = error.message;
            console.error('Login error:', errorCode, errorMessage);
        });
}

// Add an event listener to the login form
document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault(); // Prevent the default form submission
    login(); // Call the login function when the form is submitted
});

// Add a "Forgot Password" link
const forgotPasswordLink = document.getElementById('forgot_password_link');
forgotPasswordLink.addEventListener('click', () => {
    // Redirect or perform other actions for password reset
    window.location.href = '/forgot_password';
});

// You can add more functionality for handling user registration and other Firebase Authentication features as needed.
