// forms.js
// Event listeners for form submissions

import { formValidation } from './validate.js';

const forms = [
    {
        id: 'create-form',
        title: "Post create", text: "Are you sure you want to create this post?",
        auto: false,
    },
    {
        id: 'edit-form',
        title: "Post edit", text: "Are you sure you want to edit this post?",
        auto: false,
    },
    {
        id: 'delete-form',
        title: "Post deletion", text: "Are you sure you want to delete this post?",
        auto: false,
    },
    {
        id: 'login-form',
        title: "Continue login", text: "",
        auto: true, callback: formValidation.validateLogin,
    },
    {
        id: 'changepassword-form',
        title: "Change password", text: "Are you sure you want to change password?",
        auto: false, callback: formValidation.validateChangePassword,
    },
    {
        id: 'register-form',
        title: "Register", text: "Are you sure you want to register?",
        auto: false,
    },
];


export { forms };
