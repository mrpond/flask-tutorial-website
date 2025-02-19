// forms.js
// Event listeners for form submissions

const formValidation = {
    validateChangePassword() {
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const confirmNewPassword = document.getElementById('confirm-new-password').value;
        const flashDiv = document.createElement('div');

        // Assuming flashMessages is available in the context where this method is called
        const flashMessages = document.getElementById('flash-messages');
        
        // Clear any existing flash messages
        flashMessages.innerHTML = '';
        flashDiv.className = 'flash';

        // Validate current password
        if (currentPassword.length < 4) {
            flashDiv.textContent = 'Current password must be at least 4 characters long.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        // Validate new password
        if (newPassword.length < 4 || confirmNewPassword.length < 4) {
            flashDiv.textContent = 'New password must be at least 4 characters long.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        if (currentPassword === newPassword) {
            flashDiv.textContent = 'Cannot change to same password.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        // Confirm new password matches
        if (newPassword !== confirmNewPassword) {
            flashDiv.textContent = 'New passwords do not match.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        // Additional checks could be added here, like password complexity

        return flashMessages.children.length === 0;
    },

    validateLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        const flashDiv = document.createElement('div');

        // Assuming flashMessages is available in the context where this method is called
        const flashMessages = document.getElementById('flash-messages');
        
        // Clear any existing flash messages
        flashMessages.innerHTML = '';
        flashDiv.className = 'flash';

        if (!/^[a-zA-Z0-9]+$/.test(username)) {
            flashDiv.textContent = 'Username must contain only alphanumeric characters.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        if (username.length < 4) {
            flashDiv.textContent = 'Username must be at least 4 characters long.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        if (password.length < 4) {
            flashDiv.textContent = 'Password must be at least 4 characters long.';
            flashMessages.appendChild(flashDiv);
            return false;
        }

        return flashMessages.children.length === 0;
    }
};

const forms = [
    {
        id: 'create-form', target: 'cf-turnstile-create',
        title: "Post create", text: "Are you sure you want to create this post?",
        auto: false,
    },
    {
        id: 'edit-form', target: 'cf-turnstile-edit',
        title: "Post edit", text: "Are you sure you want to edit this post?",
        auto: false,
    },
    {
        id: 'delete-form', target: 'cf-turnstile-delete',
        title: "Post deletion", text: "Are you sure you want to delete this post?",
        auto: false,
    },
    {
        id: 'login-form', target: 'cf-turnstile-login',
        title: "Continue login", text: "",
        auto: true, callback: formValidation.validateLogin,
    },
    {
        id: 'changepassword-form', target: 'cf-turnstile-changepassword',
        title: "Change password", text: "Are you sure you want to change password?",
        auto: false, callback: formValidation.validateChangePassword,
    },
    {
        id: 'register-form', target: 'cf-turnstile-register',
        title: "Register", text: "Are you sure you want to register?",
        auto: false,
    },
];


export { forms, formValidation };
