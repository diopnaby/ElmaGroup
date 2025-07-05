/**
 * ELMA Group - Main JavaScript File
 * Handles interactive functionality for blog, library, and general site features
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
});

function initializeApp() {
    // Initialize all components
    initializeNewsletter();
    initializeSearch();
    initializeComments();
    initializeForms();
    initializeTooltips();
    initializeImageLazyLoading();
    initializeReadingProgress();
    initializeBackToTop();
}

// Newsletter subscription
function initializeNewsletter() {
    const newsletterForm = document.getElementById('newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            // Show loading state
            submitBtn.textContent = 'Envoi...';
            submitBtn.disabled = true;

            fetch('/newsletter/subscribe', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification(data.message, 'success');
                        this.reset();
                    } else {
                        showNotification(data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification('Une erreur est survenue. Veuillez réessayer.', 'error');
                })
                .finally(() => {
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                });
        });
    }
}

// Enhanced search functionality
function initializeSearch() {
    const searchInput = document.querySelector('input[name="q"]');
    const searchForm = document.querySelector('form[action*="search"]');

    if (searchInput && searchForm) {
        // Add search suggestions (could be enhanced with AJAX)
        searchInput.addEventListener('input', function () {
            const query = this.value.trim();
            if (query.length >= 2) {
                // Could implement search suggestions here
                // fetchSearchSuggestions(query);
            }
        });

        // Handle search form submission
        searchForm.addEventListener('submit', function (e) {
            const query = searchInput.value.trim();
            if (query.length < 2) {
                e.preventDefault();
                showNotification('Veuillez saisir au moins 2 caractères pour la recherche.', 'warning');
            }
        });
    }
}

// Comment system enhancements
function initializeComments() {
    // Initialize reply buttons
    const replyButtons = document.querySelectorAll('.comment-reply-btn');
    replyButtons.forEach(button => {
        button.addEventListener('click', function () {
            const commentId = this.dataset.commentId;
            toggleReplyForm(commentId);
        });
    });

    // Initialize comment forms
    const commentForms = document.querySelectorAll('.comment-form');
    commentForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!validateCommentForm(this)) {
                e.preventDefault();
            }
        });
    });
}

// Form validation and enhancements
function initializeForms() {
    // Contact form
    const contactForm = document.querySelector('#contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            if (!validateContactForm(this)) {
                e.preventDefault();
            }
        });
    }

    // Testimonial form
    const testimonialForm = document.querySelector('#testimonial-form');
    if (testimonialForm) {
        testimonialForm.addEventListener('submit', function (e) {
            if (!validateTestimonialForm(this)) {
                e.preventDefault();
            }
        });
    }

    // Review form
    const reviewForm = document.querySelector('#review-form');
    if (reviewForm) {
        initializeStarRating(reviewForm);
        reviewForm.addEventListener('submit', function (e) {
            if (!validateReviewForm(this)) {
                e.preventDefault();
            }
        });
    }
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Lazy loading for images
function initializeImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Reading progress indicator for blog posts
function initializeReadingProgress() {
    const progressBar = document.querySelector('.reading-progress');
    if (progressBar) {
        window.addEventListener('scroll', function () {
            const scrollTop = window.pageYOffset;
            const docHeight = document.body.scrollHeight - window.innerHeight;
            const scrollPercent = (scrollTop / docHeight) * 100;
            progressBar.style.width = scrollPercent + '%';
        });
    }
}

// Back to top button
function initializeBackToTop() {
    const backToTopBtn = document.querySelector('.back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function () {
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'block';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });

        backToTopBtn.addEventListener('click', function () {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

// Form validation functions
function validateContactForm(form) {
    const name = form.querySelector('input[name="name"]').value.trim();
    const email = form.querySelector('input[name="email"]').value.trim();
    const subject = form.querySelector('input[name="subject"]').value.trim();
    const message = form.querySelector('textarea[name="message"]').value.trim();

    if (!name) {
        showNotification('Le nom est requis.', 'error');
        return false;
    }

    if (!isValidEmail(email)) {
        showNotification('Veuillez saisir une adresse email valide.', 'error');
        return false;
    }

    if (!subject) {
        showNotification('Le sujet est requis.', 'error');
        return false;
    }

    if (!message || message.length < 10) {
        showNotification('Le message doit contenir au moins 10 caractères.', 'error');
        return false;
    }

    return true;
}

function validateCommentForm(form) {
    const name = form.querySelector('input[name="name"]').value.trim();
    const email = form.querySelector('input[name="email"]').value.trim();
    const content = form.querySelector('textarea[name="content"]').value.trim();

    if (!name) {
        showNotification('Le nom est requis.', 'error');
        return false;
    }

    if (!isValidEmail(email)) {
        showNotification('Veuillez saisir une adresse email valide.', 'error');
        return false;
    }

    if (!content || content.length < 5) {
        showNotification('Le commentaire doit contenir au moins 5 caractères.', 'error');
        return false;
    }

    if (content.length > 2000) {
        showNotification('Le commentaire ne peut pas dépasser 2000 caractères.', 'error');
        return false;
    }

    return true;
}

function validateTestimonialForm(form) {
    const quote = form.querySelector('textarea[name="quote"]').value.trim();
    const displayName = form.querySelector('input[name="display_name"]').value.trim();
    const email = form.querySelector('input[name="email"]').value.trim();
    const category = form.querySelector('select[name="category"]').value;

    if (!quote || quote.length < 10) {
        showNotification('Le témoignage doit contenir au moins 10 caractères.', 'error');
        return false;
    }

    if (quote.length > 1000) {
        showNotification('Le témoignage ne peut pas dépasser 1000 caractères.', 'error');
        return false;
    }

    if (!displayName) {
        showNotification('Le nom est requis.', 'error');
        return false;
    }

    if (!isValidEmail(email)) {
        showNotification('Veuillez saisir une adresse email valide.', 'error');
        return false;
    }

    if (!category) {
        showNotification('Veuillez sélectionner une catégorie.', 'error');
        return false;
    }

    return true;
}

function validateReviewForm(form) {
    const reviewerName = form.querySelector('input[name="reviewer_name"]').value.trim();
    const reviewerEmail = form.querySelector('input[name="reviewer_email"]').value.trim();
    const content = form.querySelector('textarea[name="content"]').value.trim();
    const rating = form.querySelector('input[name="rating"]:checked');

    if (!reviewerName) {
        showNotification('Le nom est requis.', 'error');
        return false;
    }

    if (!isValidEmail(reviewerEmail)) {
        showNotification('Veuillez saisir une adresse email valide.', 'error');
        return false;
    }

    if (!content || content.length < 10) {
        showNotification("L'avis doit contenir au moins 10 caractères.", 'error');
        return false;
    }

    if (!rating) {
        showNotification('Veuillez donner une note.', 'error');
        return false;
    }

    return true;
}

// Star rating functionality
function initializeStarRating(form) {
    const stars = form.querySelectorAll('.star-rating input[type="radio"]');
    const starLabels = form.querySelectorAll('.star-rating label');

    starLabels.forEach((label, index) => {
        label.addEventListener('mouseover', function () {
            highlightStars(starLabels, index + 1);
        });

        label.addEventListener('mouseout', function () {
            const checkedStar = form.querySelector('.star-rating input[type="radio"]:checked');
            if (checkedStar) {
                const checkedIndex = Array.from(stars).indexOf(checkedStar);
                highlightStars(starLabels, checkedIndex + 1);
            } else {
                highlightStars(starLabels, 0);
            }
        });
    });

    stars.forEach((star, index) => {
        star.addEventListener('change', function () {
            highlightStars(starLabels, index + 1);
        });
    });
}

function highlightStars(starLabels, count) {
    starLabels.forEach((label, index) => {
        const icon = label.querySelector('i');
        if (index < count) {
            icon.className = 'fas fa-star text-warning';
        } else {
            icon.className = 'far fa-star text-muted';
        }
    });
}

// Reply form toggle
function toggleReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        if (replyForm.style.display === 'none' || !replyForm.style.display) {
            replyForm.style.display = 'block';
            replyForm.querySelector('input[name="parent_id"]').value = commentId;
        } else {
            replyForm.style.display = 'none';
        }
    }
}

// Utility functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';

    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function formatPrice(price, currency = 'XOF') {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0
    }).format(price);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.ElmaApp = {
    showNotification,
    validateContactForm,
    validateCommentForm,
    validateTestimonialForm,
    validateReviewForm,
    initializeStarRating,
    toggleReplyForm,
    isValidEmail,
    formatPrice,
    debounce
};

// Blog specific functionality
if (document.body.classList.contains('blog-page')) {
    // Initialize blog-specific features
    initializeBlogFeatures();
}

function initializeBlogFeatures() {
    // Social sharing
    initializeSocialSharing();

    // Table of contents
    generateTableOfContents();

    // Estimated reading time update
    updateReadingTime();
}

function initializeSocialSharing() {
    const shareButtons = document.querySelectorAll('.social-share-btn');
    shareButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const platform = this.dataset.platform;
            const url = encodeURIComponent(window.location.href);
            const title = encodeURIComponent(document.title);

            let shareUrl = '';

            switch (platform) {
                case 'facebook':
                    shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                    break;
                case 'twitter':
                    shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                    break;
                case 'linkedin':
                    shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
                    break;
            }

            if (shareUrl) {
                window.open(shareUrl, 'share', 'width=600,height=400');
            }
        });
    });
}

function generateTableOfContents() {
    const content = document.querySelector('.blog-content');
    const tocContainer = document.querySelector('.table-of-contents');

    if (content && tocContainer) {
        const headings = content.querySelectorAll('h2, h3, h4');
        if (headings.length > 0) {
            const tocList = document.createElement('ul');
            tocList.className = 'list-unstyled';

            headings.forEach((heading, index) => {
                const id = `heading-${index}`;
                heading.id = id;

                const listItem = document.createElement('li');
                listItem.className = `toc-${heading.tagName.toLowerCase()}`;

                const link = document.createElement('a');
                link.href = `#${id}`;
                link.textContent = heading.textContent;
                link.className = 'text-decoration-none';

                listItem.appendChild(link);
                tocList.appendChild(listItem);
            });

            tocContainer.appendChild(tocList);
        }
    }
}

function updateReadingTime() {
    const content = document.querySelector('.blog-content');
    const readingTimeElement = document.querySelector('.reading-time-value');

    if (content && readingTimeElement) {
        const text = content.textContent || content.innerText || '';
        const wordCount = text.trim().split(/\s+/).length;
        const readingTime = Math.ceil(wordCount / 200); // 200 words per minute

        readingTimeElement.textContent = `${readingTime} min`;
    }
}

console.log('🎉 ELMA Group application initialized successfully!');

// Enhanced Back to Top functionality for professional footer
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Enhanced footer newsletter functionality
document.addEventListener('DOMContentLoaded', function () {
    // Enhanced back to top button
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function () {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });
    }

    // Footer newsletter form enhancement
    const footerNewsletterForm = document.querySelector('.footer-newsletter form');
    if (footerNewsletterForm) {
        footerNewsletterForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const emailInput = this.querySelector('input[type="email"]');
            const submitBtn = this.querySelector('button[type="submit"]');
            const email = emailInput.value.trim();

            if (!email) {
                showNotification('Veuillez saisir votre adresse email.', 'warning');
                return;
            }

            if (!isValidEmail(email)) {
                showNotification('Veuillez saisir une adresse email valide.', 'error');
                return;
            }

            // Show loading state
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Envoi...';
            submitBtn.disabled = true;

            // Simulate newsletter subscription (replace with actual endpoint)
            setTimeout(() => {
                showNotification('Merci pour votre inscription à notre newsletter !', 'success');
                emailInput.value = '';
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 1500);
        });
    }

    // Footer social links analytics tracking
    const socialLinks = document.querySelectorAll('.footer-social-links a');
    socialLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const platform = this.getAttribute('aria-label') || 'Unknown';
            console.log(`Social link clicked: ${platform}`);
            // Add analytics tracking here if needed
        });
    });
});

// Footer links smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function () {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

console.log('🚀 Professional footer functionality initialized!');
