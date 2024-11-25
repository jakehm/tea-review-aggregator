document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    const removeButton = document.getElementById('remove-image');

    if (imageInput) {
        imageInput.addEventListener('change', previewImage);
    }

    if (removeButton) {
        removeButton.addEventListener('click', function(e) {
            e.preventDefault();
            imagePreview.style.display = 'none';
            const img = imagePreview.querySelector('img');
            if (img) {
                img.remove();
            }
            imageInput.value = '';
        });
    }

    function previewImage(event) {
        const file = event.target.files[0];
        
        if (file) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                // Create an image element if it doesn't exist
                let img = imagePreview.querySelector('img');
                if (!img) {
                    img = document.createElement('img');
                    imagePreview.appendChild(img);
                }
                
                // Set the image source
                img.src = e.target.result;
                imagePreview.style.display = 'block';
            }
            
            reader.readAsDataURL(file);
        } else {
            imagePreview.style.display = 'none';
        }
    }
});
