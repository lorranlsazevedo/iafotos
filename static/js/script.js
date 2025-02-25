let selectedFiles = [];
let currentCropper = null;
let currentImageIndex = null;

const dropZone = document.getElementById('dropZone');
const selectAllCheckbox = document.getElementById('selectAll');
const deleteSelectedButton = document.getElementById('deleteSelected');
const selectionControls = document.querySelector('.selection-controls');
const previewArea = document.getElementById('imagePreview');
const loadingOverlay = document.querySelector('.loading-overlay');
const processButton = document.getElementById('processButton');
const processBlurButton = document.getElementById('processBlurButton');
const dateInput = document.getElementById('dateInput');

// Previne o comportamento padrão de drag & drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Adiciona visual feedback
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropZone.classList.add('drag-over');
}

function unhighlight(e) {
    dropZone.classList.remove('drag-over');
}

// Handle dropped files
dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const newFiles = [...dt.files];

    // Verifica o limite total de imagens
    if (selectedFiles.length + newFiles.length > 25) {
        alert('O número total de imagens não pode exceder 25.');
        return;
    }

    // Concatena as novas imagens com as existentes
    selectedFiles = [...selectedFiles, ...newFiles];
    displayPreviews(selectedFiles);
    updateProcessButton();
}

function handleFiles(files) {
    // Converte FileList para Array e concatena com as imagens existentes
    const newFiles = [...files];

    // Verifica o limite total de imagens
    if (selectedFiles.length + newFiles.length > 25) {
        alert('O número de imagens não pode exceder 25.');
        return;
    }

    // Concatena as novas imagens com as existentes
    selectedFiles = [...selectedFiles, ...newFiles];
    displayPreviews(selectedFiles);
    updateProcessButton();
}

document.getElementById('imageInput').addEventListener('change', handleFileSelect);
processButton.addEventListener('click', processImages);
processBlurButton.addEventListener('click', processBlurImages);
document.getElementById('downloadButton').addEventListener('click', downloadImages);

function handleFileSelect(event) {
    const newFiles = Array.from(event.target.files);

    // Verifica o limite total de imagens
    if (selectedFiles.length + newFiles.length > 25) {
        alert('O número total de imagens não pode exceder 25.');
        return;
    }

    // Concatena as novas imagens com as existentes
    selectedFiles = [...selectedFiles, ...newFiles];
    displayPreviews(selectedFiles);
    updateProcessButton();

    // Limpa o input para permitir selecionar o mesmo arquivo novamente
    event.target.value = '';
}

// Função para verificar se todos os elementos necessários existem
function checkRequiredElements() {
    const elements = {
        dropZone,
        selectAllCheckbox,
        deleteSelectedButton,
        selectionControls,
        previewArea,
        loadingOverlay
    };

    for (const [name, element] of Object.entries(elements)) {
        if (!element) {
            console.error(`Elemento não encontrado: ${name}`);
            return false;
        }
    }
    return true;
}

function displayPreviews(files) {
    if (!checkRequiredElements()) {
        console.error('Elementos necessários não encontrados');
        return;
    }

    // Mostrar loading
    loadingOverlay.style.display = 'flex';
    previewArea.innerHTML = '';

    // Só mostrar os controles de seleção se houver arquivos
    if (files && files.length > 0) {
        selectionControls.style.display = 'flex';
    } else {
        selectionControls.style.display = 'none';
    }

    const promises = files.map((file, index) => {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = function (e) {
                const container = document.createElement('div');
                container.className = 'preview-container';

                // Checkbox para seleção
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'select-checkbox';
                checkbox.addEventListener('change', updateDeleteButton);

                const img = document.createElement('img');
                img.src = e.target.result;

                const editButton = document.createElement('button');
                editButton.className = 'edit-button';
                editButton.textContent = 'Editar';
                editButton.onclick = () => openCropModal(index);

                container.appendChild(checkbox);
                container.appendChild(img);
                container.appendChild(editButton);
                previewArea.appendChild(container);
                setTimeout(resolve, 500);
            };
            reader.readAsDataURL(file);
        });
    });

    // Esconder loading quando todas as imagens forem carregadas
    Promise.all(promises).then(() => {
        loadingOverlay.style.display = 'none';
        updateProcessButton();
    });
}

function updateDeleteButton() {
    if (!deleteSelectedButton) return;

    const selectedCheckboxes = document.querySelectorAll('.select-checkbox:checked');
    deleteSelectedButton.disabled = selectedCheckboxes.length === 0;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    if (!checkRequiredElements()) return;

    selectAllCheckbox.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.select-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = e.target.checked;
            checkbox.closest('.preview-container').classList.toggle('selected', e.target.checked);
        });
        updateDeleteButton();
    });

    deleteSelectedButton.addEventListener('click', () => {
        const newFiles = [];
        const checkboxes = document.querySelectorAll('.select-checkbox');

        selectedFiles.forEach((file, index) => {
            if (!checkboxes[index].checked) {
                newFiles.push(file);
            }
        });

        selectedFiles = newFiles;

        if (selectedFiles.length === 0) {
            selectionControls.style.display = 'none';
        }

        displayPreviews(selectedFiles);
        updateProcessButton();
    });
});

function openCropModal(index) {
    currentImageIndex = index;
    const modal = document.getElementById('cropModal');
    const cropImage = document.getElementById('cropImage');

    const reader = new FileReader();
    reader.onload = function (e) {
        cropImage.src = e.target.result;
        modal.style.display = 'block';

        if (currentCropper) {
            currentCropper.destroy();
        }

        currentCropper = new Cropper(cropImage, {
            aspectRatio: NaN, // Livre
            viewMode: 1,
            autoCropArea: 1,
        });
    }
    reader.readAsDataURL(selectedFiles[index]);
}

// Fechar modal
document.querySelector('.close').onclick = function () {
    document.getElementById('cropModal').style.display = 'none';
    if (currentCropper) {
        currentCropper.destroy();
        currentCropper = null;
    }
}

// Botão de cortar
document.getElementById('cropButton').onclick = function () {
    if (!currentCropper) return;

    const canvas = currentCropper.getCroppedCanvas();
    canvas.toBlob((blob) => {
        const file = new File([blob], selectedFiles[currentImageIndex].name, {
            type: 'image/jpeg',
            lastModified: new Date().getTime()
        });

        selectedFiles[currentImageIndex] = file;
        displayPreviews(selectedFiles);

        document.getElementById('cropModal').style.display = 'none';
        currentCropper.destroy();
        currentCropper = null;
    }, 'image/jpeg');
}

async function processImages() {
    const date = document.getElementById('dateInput').value;
    const processButton = document.getElementById('processButton');
    const buttonContent = processButton.querySelector('.button-content');
    const buttonLoader = processButton.querySelector('.button-loader');

    // Mostrar loading
    buttonContent.style.display = 'none';
    buttonLoader.style.display = 'block';
    processButton.disabled = true;

    try {
        const processedImages = [];

        for (const file of selectedFiles) {
            const img = await createImage(file);
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = img.width;
            canvas.height = img.height;

            // Desenhar a imagem
            ctx.drawImage(img, 0, 0);

            // Só adicionar a legenda se ela existir
            if (date.trim()) {
                // Configurar o estilo do texto
                ctx.font = '20px Arial';

                // Calcular a largura do texto
                const textWidth = ctx.measureText(date).width;
                const padding = 5;

                // Posicionar o texto
                const xPosition = canvas.width - textWidth - 10;
                const yPosition = 25;

                // Desenhar o fundo branco
                ctx.fillStyle = 'white';
                ctx.fillRect(
                    xPosition - padding,
                    yPosition - 20,
                    textWidth + (padding * 2),
                    30
                );

                // Desenhar o texto
                ctx.fillStyle = 'black';
                ctx.fillText(date, xPosition, yPosition);
            }

            processedImages.push({
                name: file.name,
                data: canvas.toDataURL('image/jpeg', 0.9)
            });
        }

        document.getElementById('downloadButton').disabled = false;
        window.processedImages = processedImages;
    } catch (error) {
        alert('Erro ao processar as imagens: ' + error.message);
    } finally {
        // Esconder loading
        buttonContent.style.display = 'block';
        buttonLoader.style.display = 'none';
        processButton.disabled = false;
    }
}

function createImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = URL.createObjectURL(file);
    });
}

async function downloadImages() {
    const zip = new JSZip();
    const processedImages = window.processedImages;

    processedImages.forEach((image, index) => {
        const base64Data = image.data.replace(/^data:image\/\w+;base64,/, "");
        zip.file(`processed_${image.name}`, base64Data, { base64: true });
    });

    const content = await zip.generateAsync({ type: "blob" });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(content);
    link.download = 'processed_images.zip';
    link.click();
}

// Atualizar o botão de processar
function updateProcessButton() {
    if (!processButton || !dateInput) return;

    const hasImages = selectedFiles.length > 0;
    processButton.disabled = !hasImages;
    processBlurButton.disabled = !hasImages;
}

if (dateInput) {
    dateInput.addEventListener('input', updateProcessButton);
}

async function processBlurImages() {
    console.log("processBlurImages iniciada");
    const buttonContent = processBlurButton.querySelector('.button-content');
    const buttonLoader = processBlurButton.querySelector('.button-loader');

    // Exibe loading e desabilita o botão
    buttonContent.style.display = 'none';
    buttonLoader.style.display = 'block';
    processBlurButton.disabled = true;

    try {
        const formData = new FormData();
        // Adiciona todas as imagens selecionadas
        for (const file of selectedFiles) {
            formData.append('images', file);
        }

        console.log("Enviando imagens para /process_blur_resize");
        const response = await fetch('/process_blur_resize', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Erro no processamento das imagens.');
        }

        const blob = await response.blob();
        console.log("Processamento concluído, iniciando download");

        // Cria link para download do ZIP retornado
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'imagens_borradas_redimensionadas.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (error) {
        alert('Erro ao processar as imagens: ' + error.message);
        console.error(error);
    } finally {
        // Reabilita o botão ao final do processamento
        buttonContent.style.display = 'block';
        buttonLoader.style.display = 'none';
        processBlurButton.disabled = false;
        console.log("processBlurImages finalizada");
    }
}

// Certifique-se de adicionar o event listener para o botão de borrar:
processBlurButton.addEventListener('click', processBlurImages);