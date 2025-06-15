document.addEventListener('DOMContentLoaded', function() {
    // Text Summarization Form Handlers
    const urlForm = document.getElementById('urlForm');
    const topicForm = document.getElementById('topicForm');
    const loadingContainer = document.getElementById('loadingContainer');
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    const errorText = document.getElementById('errorText');
    const summaryText = document.getElementById('summaryText');
    const newSearchBtn = document.getElementById('newSearchBtn');

    // Text summarization via URL
    if (urlForm) {
        urlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const url = document.getElementById('urlInput').value;
            if (!url) return;

            // Show loading state
            loadingContainer.classList.remove('d-none');
            resultContainer.classList.add('d-none');
            errorContainer.classList.add('d-none');

            // Make API request
            fetch('/summarize-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url }),
            })
            .then(response => response.json())
            .then(data => {
                loadingContainer.classList.add('d-none');
                
                if (data.error) {
                    errorText.textContent = data.error;
                    errorContainer.classList.remove('d-none');
                } else {
                    summaryText.textContent = data.summary;
                    resultContainer.classList.remove('d-none');
                }
            })
            .catch(error => {
                loadingContainer.classList.add('d-none');
                errorText.textContent = 'An error occurred while processing your request. Please try again.';
                errorContainer.classList.remove('d-none');
                console.error('Error:', error);
            });
        });
    }

    // Text summarization via Topic
    if (topicForm) {
        topicForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const topic = document.getElementById('topicInput').value;
            if (!topic) return;

            // Show loading state
            loadingContainer.classList.remove('d-none');
            resultContainer.classList.add('d-none');
            errorContainer.classList.add('d-none');

            // Make API request
            fetch('/summarize-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic: topic }),
            })
            .then(response => response.json())
            .then(data => {
                loadingContainer.classList.add('d-none');
                
                if (data.error) {
                    errorText.textContent = data.error;
                    errorContainer.classList.remove('d-none');
                } else {
                    summaryText.textContent = data.summary;
                    resultContainer.classList.remove('d-none');
                }
            })
            .catch(error => {
                loadingContainer.classList.add('d-none');
                errorText.textContent = 'An error occurred while processing your request. Please try again.';
                errorContainer.classList.remove('d-none');
                console.error('Error:', error);
            });
        });
    }

    // Reset button for new search
    if (newSearchBtn) {
        newSearchBtn.addEventListener('click', function() {
            resultContainer.classList.add('d-none');
            if (urlForm) urlForm.reset();
            if (topicForm) topicForm.reset();
        });
    }

    // Video Summarization Handlers
    const videoUrlForm = document.getElementById('videoUrlForm');
    const videoUploadForm = document.getElementById('videoUploadForm');
    const videoLoadingContainer = document.getElementById('videoLoadingContainer');
    const videoResultContainer = document.getElementById('videoResultContainer');
    const videoErrorContainer = document.getElementById('videoErrorContainer');
    const videoErrorText = document.getElementById('videoErrorText');
    const videoSummaryText = document.getElementById('videoSummaryText');
    const newVideoBtn = document.getElementById('newVideoBtn');
    const videoDisplay = document.getElementById('videoDisplay');
    const youtubeEmbed = document.getElementById('youtubeEmbed');

    // Video summarization via URL
    if (videoUrlForm) {
        videoUrlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            videoLoadingContainer.classList.remove('d-none');
            videoResultContainer.classList.add('d-none');
            videoErrorContainer.classList.add('d-none');

            // Get form data
            const formData = new FormData(videoUrlForm);
            
            // Make API request
            fetch('/summarize-video-url', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                videoLoadingContainer.classList.add('d-none');
                
                if (data.error) {
                    videoErrorText.textContent = data.error;
                    videoErrorContainer.classList.remove('d-none');
                } else {
                    videoSummaryText.textContent = data.summary;
                    videoResultContainer.classList.remove('d-none');
                    
                    // If we have a video URL, show it in an iframe
                    if (data.video_url && data.video_url.includes('youtube.com')) {
                        const videoId = extractYoutubeId(data.video_url);
                        if (videoId) {
                            youtubeEmbed.src = `https://www.youtube.com/embed/${videoId}`;
                            videoDisplay.classList.remove('d-none');
                        }
                    }
                }
            })
            .catch(error => {
                videoLoadingContainer.classList.add('d-none');
                videoErrorText.textContent = 'An error occurred while processing your request. Please try again.';
                videoErrorContainer.classList.remove('d-none');
                console.error('Error:', error);
            });
        });
    }

    // Video summarization via file upload
    if (videoUploadForm) {
        videoUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            videoLoadingContainer.classList.remove('d-none');
            videoResultContainer.classList.add('d-none');
            videoErrorContainer.classList.add('d-none');
            
            // Get form data
            const formData = new FormData(videoUploadForm);
            
            // Make API request
            fetch('/summarize-video', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                videoLoadingContainer.classList.add('d-none');
                
                if (data.error) {
                    videoErrorText.textContent = data.error;
                    videoErrorContainer.classList.remove('d-none');
                } else {
                    videoSummaryText.textContent = data.summary;
                    videoResultContainer.classList.remove('d-none');
                    videoDisplay.classList.add('d-none'); // Hide video display for uploads
                }
            })
            .catch(error => {
                videoLoadingContainer.classList.add('d-none');
                videoErrorText.textContent = 'An error occurred while processing your request. Please try again.';
                videoErrorContainer.classList.remove('d-none');
                console.error('Error:', error);
            });
        });
    }

    // Reset button for new video search
    if (newVideoBtn) {
        newVideoBtn.addEventListener('click', function() {
            videoResultContainer.classList.add('d-none');
            videoDisplay.classList.add('d-none');
            youtubeEmbed.src = "";
            if (videoUrlForm) videoUrlForm.reset();
            if (videoUploadForm) videoUploadForm.reset();
        });
    }

    // Helper function to extract YouTube video ID
    function extractYoutubeId(url) {
        const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
        const match = url.match(regExp);
        return (match && match[7].length === 11) ? match[7] : null;
    }

    // Initialize any Bootstrap components
    // Enable tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
});
