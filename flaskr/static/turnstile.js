// Turnstile.js
import { forms, formValidation } from './forms.js';

class TurnstileManager {
    constructor() {
        this.turnstileWidgetId = null;
        this.forms = forms;
        this.modalBackdrop = document.getElementById('modal-backdrop');
        this.modalContent = document.getElementById('modal-content');
        this.turnstileContainerId = 'cf-container';
        this.confirmButton = document.getElementById('confirm-action');
        this.cancelButton = document.getElementById('cancel-action');
    }

    showModal(form) {
        const title = document.getElementById('modal-title');
        const text = document.getElementById('modal-text');
        const turnstileTokenContainerId = form.target;

        const cfSiteKeyMeta = document.querySelector('meta[name="cf-turnstile-site-key"]');
        let cf_site_key = cfSiteKeyMeta.getAttribute('content')

        if (form.site_key)
            cf_site_key = document.getElementById(form.site_key)?.value;

        document.getElementById('modal-title');

        title.textContent = form.title;
        text.textContent = form.text;

        if (form.auto === true) {
            this.cancelButton.style.display = 'none';
        }
        this.confirmButton.style.display = 'none';
        this.confirmButton.onclick = () => this.submitForm(form.id);

        // show the turnstile widget
        this.turnstileWidgetId = turnstile.render(`#${this.turnstileContainerId}`, {
            sitekey: cf_site_key,
            action: form.id,
            callback: (token) => {
                document.getElementById(turnstileTokenContainerId).value = token;
                console.log(`Challenge Success ${token}`);
                if (form.auto === true) {
                    this.submitForm(form.id);
                }
                this.confirmButton.style.display = '';
            },
            'expired-callback': () => console.log('Challenge expired'),
            'error-callback': () => console.log('An error occurred with Turnstile'),
            'challenge-shown': () => console.log('Challenge requires user interaction')
        });
        // Show the modal
        this.modalBackdrop.style.display = 'block';
        this.modalContent.style.display = 'block';
    }

    submitForm(formId) {
        document.getElementById(formId).submit();
        this.closeModal();
    }

    closeModal() {
        this.modalBackdrop.style.display = 'none';
        this.modalContent.style.display = 'none';
        turnstile.remove(this.turnstileWidgetId);
    }

    initialize() {
        this.forms.forEach(form => {
            const element = document.getElementById(form.id);
            if (!element) {
                return;
            }
            element.addEventListener('submit', (e) => {
                e.preventDefault();
                if (form.callback && typeof (form.callback) === 'function') {
                    if (form.callback() === true) {
                        this.showModal(form);
                    }
                } else {
                    this.showModal(form);
                }
            });
        });
        this.cancelButton.onclick = () => this.closeModal();
    }
}

// Export the class for use in other modules
export default TurnstileManager;