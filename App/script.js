// Función para guardar el curso académico
function saveCurso() {
    const cursoSelect = document.getElementById('cursoSelect');
    localStorage.setItem('alumno_curso', cursoSelect.value);
}

// Función para guardar el curso académico
function saveCurso() {
    const cursoSelect = document.getElementById('cursoSelect');
    localStorage.setItem('alumno_curso', cursoSelect.value);
}

// Función para manejar el switch de transporte
function toggleTransporte() {
    const transporteSwitch = document.getElementById('transporteSwitch');
    const transporteLabel = document.getElementById('transporteLabel');
    
    if (transporteSwitch.checked) {
        transporteLabel.textContent = 'Sí';
        transporteLabel.style.color = '#7EB900';
    } else {
        transporteLabel.textContent = 'No';
        transporteLabel.style.color = '#666';
    }
}

// Función para guardar el perfil completo
function saveProfile() {
    const transporteSwitch = document.getElementById('transporteSwitch');
    const transporteValue = transporteSwitch.checked ? 'Sí' : 'No';
    
    localStorage.setItem('alumno_transporte', transporteValue);
    
    // Mostrar mensaje de confirmación
    alert('✅ Perfil guardado correctamente');
}

// Función para cargar la foto de perfil
function loadPhoto(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById('profilePhoto');
            img.src = e.target.result;
            // Guardar en localStorage
            localStorage.setItem('alumno_photo', e.target.result);
        }
        reader.readAsDataURL(file);
    }
}

// Variable para guardar el campo que se está editando
let currentField = '';

// Función para abrir el modal de edición
function openEditModal(fieldName) {
    currentField = fieldName;
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalLabel = document.getElementById('modalLabel');
    const modalInput = document.getElementById('modalInput');
    
    // Configurar el modal según el campo
    const fieldLabels = {
        'nombre': 'Nombre',
        'apellidos': 'Apellidos',
        'localidad': 'Localidad',
        'instituto': 'Instituto',
        'intereses': 'Intereses'
    };
    
    modalTitle.textContent = `Editar ${fieldLabels[fieldName]}`;
    modalLabel.textContent = `${fieldLabels[fieldName]}:`;
    
    // Cargar el valor actual
    const currentValue = document.getElementById(`${fieldName}Value`).textContent;
    modalInput.value = currentValue;
    
    modal.style.display = 'block';
    modalInput.focus();
}

// Función para cerrar el modal
function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.style.display = 'none';
    currentField = '';
}

// Función para guardar el campo editado
function saveField() {
    const modalInput = document.getElementById('modalInput');
    const newValue = modalInput.value.trim();
    
    // Detectar si es profesor o alumno
    if (window.currentEditFieldTeacher) {
        // Guardar campo del profesor
        saveFieldTeacher();
        return;
    }
    
    if (newValue) {
        document.getElementById(`${currentField}Value`).textContent = newValue;
        
        // Guardar en localStorage
        localStorage.setItem(`alumno_${currentField}`, newValue);
    }
    
    closeEditModal();
}

// Cerrar modal al hacer clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target === modal) {
        closeEditModal();
    }
}

// Función para seleccionar pestaña
function selectTab(tabName) {
    // Ocultar todos los contenidos de pestañas
    document.getElementById('perfilContent').style.display = 'none';
    document.getElementById('contenidoContent').style.display = 'none';
    document.getElementById('salidasContent').style.display = 'none';
    
    // Remover clase active de todos los botones
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Mostrar contenido seleccionado y marcar botón como activo
    if (tabName === 'perfil') {
        document.getElementById('perfilContent').style.display = 'block';
        tabButtons[0].classList.add('active');
    } else if (tabName === 'contenido') {
        document.getElementById('contenidoContent').style.display = 'block';
        tabButtons[1].classList.add('active');
    } else if (tabName === 'salidas') {
        document.getElementById('salidasContent').style.display = 'block';
        tabButtons[2].classList.add('active');
    }
}

// Función para manejar el toggle del slider
function toggleUser() {
    const toggle = document.getElementById('userToggle');
    const labels = document.querySelectorAll('.toggle-label');
    
    if (toggle.checked) {
        // Modo profesor
        selectUser('profesor');
        labels[0].classList.remove('active');
        labels[1].classList.add('active');
    } else {
        // Modo alumno
        selectUser('alumno');
        labels[0].classList.add('active');
        labels[1].classList.remove('active');
    }
}

// Función para seleccionar el tipo de usuario
function selectUser(userType) {
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dashboard = document.getElementById('dashboard');
    const welcomeMessage = document.getElementById('welcomeMessage');
    
    // Si no se selecciona nada, mostrar welcome screen
    if (!userType) {
        welcomeScreen.style.display = 'block';
        dashboard.style.display = 'none';
        return;
    }
    
    // Ocultar pantalla de bienvenida
    welcomeScreen.style.display = 'none';
    
    // Mostrar dashboard
    dashboard.style.display = 'block';
    
    // Configurar mensajes según el tipo de usuario
    if (userType === 'alumno') {
        welcomeMessage.textContent = '👋 ¡Hola, Rafa!';
        
        // Mostrar panel integrado para alumno
        const integratedPanel = document.getElementById('integratedPanel');
        const teacherIntegratedPanel = document.getElementById('teacherIntegratedPanel');
        integratedPanel.style.display = 'block';
        teacherIntegratedPanel.style.display = 'none';
        
        // Cargar datos del alumno
        loadStudentData();
    } else if (userType === 'profesor') {
        welcomeMessage.textContent = '👋 ¡Hola, Rafael!';
        
        // Mostrar panel integrado para profesor
        const integratedPanel = document.getElementById('integratedPanel');
        const teacherIntegratedPanel = document.getElementById('teacherIntegratedPanel');
        integratedPanel.style.display = 'none';
        teacherIntegratedPanel.style.display = 'block';
        
        // Cargar datos del profesor
        loadTeacherData();
    }
    
    // Guardar el tipo de usuario en sessionStorage
    sessionStorage.setItem('userType', userType);
}

// Función para cerrar sesión
function logout() {
    const welcomeScreen = document.getElementById('welcomeScreen');
    const dashboard = document.getElementById('dashboard');
    const userTypeSelect = document.getElementById('userType');
    
    // Ocultar dashboard
    dashboard.style.display = 'none';
    
    // Mostrar pantalla de bienvenida
    welcomeScreen.style.display = 'block';
    
    // Resetear selector
    userTypeSelect.value = '';
    
    // Limpiar sessionStorage
    sessionStorage.removeItem('userType');
}

// Verificar si hay una sesión activa al cargar la página
window.addEventListener('load', () => {
    const userType = sessionStorage.getItem('userType');
    const toggle = document.getElementById('userToggle');
    const labels = document.querySelectorAll('.toggle-label');
    
    // Cargar datos del perfil guardados
    const savedNombre = localStorage.getItem('alumno_nombre');
    const savedApellidos = localStorage.getItem('alumno_apellidos');
    const savedLocalidad = localStorage.getItem('alumno_localidad');
    const savedInstituto = localStorage.getItem('alumno_instituto');
    const savedCurso = localStorage.getItem('alumno_curso');
    const savedTransporte = localStorage.getItem('alumno_transporte');
    const savedIntereses = localStorage.getItem('alumno_intereses');
    const savedPhoto = localStorage.getItem('alumno_photo');
    
    if (savedNombre) document.getElementById('nombreValue').textContent = savedNombre;
    if (savedApellidos) document.getElementById('apellidosValue').textContent = savedApellidos;
    if (savedLocalidad) document.getElementById('localidadValue').textContent = savedLocalidad;
    if (savedInstituto) document.getElementById('institutoValue').textContent = savedInstituto;
    if (savedCurso) document.getElementById('cursoSelect').value = savedCurso;
    if (savedIntereses) document.getElementById('interesesValue').textContent = savedIntereses;
    
    // Cargar estado del transporte
    const transporteSwitch = document.getElementById('transporteSwitch');
    const transporteLabel = document.getElementById('transporteLabel');
    if (savedTransporte === 'Sí') {
        transporteSwitch.checked = true;
        transporteLabel.textContent = 'Sí';
        transporteLabel.style.color = '#7EB900';
    }
    
    // Cargar foto guardada
    if (savedPhoto) {
        document.getElementById('profilePhoto').src = savedPhoto;
    }
    
    if (userType === 'profesor') {
        toggle.checked = true;
        labels[0].classList.remove('active');
        labels[1].classList.add('active');
        selectUser(userType);
    } else if (userType === 'alumno') {
        toggle.checked = false;
        labels[0].classList.add('active');
        labels[1].classList.remove('active');
        selectUser(userType);
    } else {
        // Por defecto, mostrar como alumno
        labels[0].classList.add('active');
    }
    
    // Cerrar modales al hacer clic fuera de ellos
    window.onclick = function(event) {
        const editModal = document.getElementById('editModal');
        const documentsModal = document.getElementById('documentsModal');
        const correctionModal = document.getElementById('correctionModal');
        
        if (event.target === editModal) {
            closeEditModal();
        }
        if (event.target === documentsModal) {
            closeDocumentsModal();
        }
        if (event.target === correctionModal) {
            closeCorrectionModal();
        }
    };
});

// Función para abrir el contenido de una asignatura
function openSubject(subjectId) {
    console.log('Abriendo asignatura:', subjectId);
    
    // Documentos por asignatura con agrupación por unidades
    const documents = {
        'biologia': [
            {
                unit: 'Animales Vertebrados',
                materials: [
                    { name: 'Temario', file: 'Animales vertebrados.pdf', type: 'pdf', size: '2.3 MB', hasCorrection: false },
                    { name: 'Ejercicios', file: 'Exercises.html', type: 'html', size: '1.8 MB', hasCorrection: true },
                    { name: 'Trabajo Monográfico', file: 'Trabajo Monográfico.pdf', type: 'pdf', size: '3.5 MB', hasCorrection: true }
                ]
            }
        ]
    };
    
    const subjectNames = {
        'biologia': 'Biología',
        'matematicas': 'Matemáticas',
        'tecnologia': 'Tecnología',
        'fisica': 'Física',
        'quimica': 'Química',
        'educacion-fisica': 'Educación Física',
        'castellano': 'Castellano',
        'ingles': 'Inglés',
        'frances': 'Francés'
    };
    
    const subjectDocs = documents[subjectId] || [];
    
    if (subjectDocs.length > 0) {
        openDocumentsModal(subjectNames[subjectId], subjectDocs);
    }
}

// Abrir modal de documentos
function openDocumentsModal(subjectName, units) {
    const modal = document.getElementById('documentsModal');
    const title = document.getElementById('documentsModalTitle');
    const list = document.getElementById('documentsList');
    
    title.textContent = `${subjectName} - Unidades`;
    
    // Limpiar lista
    list.innerHTML = '';
    
    // Crear elementos por unidad
    units.forEach(unit => {
        // Título de la unidad
        const unitTitle = document.createElement('div');
        unitTitle.className = 'unit-title';
        unitTitle.textContent = unit.unit;
        list.appendChild(unitTitle);
        
        // Materiales de la unidad
        unit.materials.forEach(material => {
            const docItem = document.createElement('div');
            docItem.className = 'document-item';
            
            const correctionBtn = material.hasCorrection ? `
                <button class="document-action-btn btn-correction" onclick="openCorrectionUpload('${material.name}')">
                    ✏️ Corrección
                </button>
            ` : '';
            
            docItem.innerHTML = `
                <div class="document-icon">📚</div>
                <div class="document-info">
                    <div class="document-name">${material.name}</div>
                    <div class="document-meta">${material.type.toUpperCase()} • ${material.size}</div>
                </div>
                <div class="document-actions">
                    <button class="document-action-btn btn-view" onclick="viewDocument('${material.file}')">
                        👁️ Visualizar
                    </button>
                    ${correctionBtn}
                </div>
            `;
            
            list.appendChild(docItem);
        });
    });
    
    modal.style.display = 'block';
}

// Cerrar modal de documentos
function closeDocumentsModal() {
    const modal = document.getElementById('documentsModal');
    modal.style.display = 'none';
}

// Visualizar documento
function viewDocument(docName) {
    console.log('Visualizando documento:', docName);
    // Convertir el nombre del PDF a HTML
    const htmlName = docName.replace('.pdf', '.html');
    // Construir ruta del documento HTML en la carpeta links
    const docPath = `links/${htmlName}`;
    // Abrir en nueva ventana
    window.open(docPath, '_blank');
}

// Descargar documento
function downloadDocument(docName) {
    console.log('Descargando documento:', docName);
    // Construir ruta del documento
    const docPath = `documents/${docName}`;
    // Crear elemento de descarga temporal
    const link = document.createElement('a');
    link.href = docPath;
    link.download = docName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Abrir modal de corrección
function openCorrectionUpload(materialName) {
    const modal = document.getElementById('correctionModal');
    const title = document.getElementById('correctionModalTitle');
    const materialNameSpan = document.getElementById('correctionMaterialName');
    
    materialNameSpan.textContent = materialName;
    modal.style.display = 'block';
}

// Cerrar modal de corrección
function closeCorrectionModal() {
    const modal = document.getElementById('correctionModal');
    const fileInput = document.getElementById('correctionFileInput');
    fileInput.value = ''; // Limpiar input
    modal.style.display = 'none';
}

// Subir documento para corrección
function uploadCorrection() {
    const fileInput = document.getElementById('correctionFileInput');
    const materialName = document.getElementById('correctionMaterialName').textContent;
    
    if (fileInput.files.length === 0) {
        alert('Por favor, selecciona un archivo para subir.');
        return;
    }
    
    const file = fileInput.files[0];
    console.log(`Subiendo archivo para corrección: ${file.name}`);
    console.log(`Material: ${materialName}`);
    
    // Aquí se implementaría la lógica de subida al servidor
    // Por ahora simulamos la subida
    alert(`✅ Archivo "${file.name}" subido correctamente para corrección de ${materialName}.\n\nRecibirás la corrección en tu perfil próximamente.`);
    
    closeCorrectionModal();
}

// Marcar grado como favorito
function marcarFavorito(button, grado, instituto) {
    button.classList.toggle('active');
    
    if (button.classList.contains('active')) {
        button.innerHTML = '⭐';
        console.log(`Grado marcado como favorito: ${grado} - ${instituto}`);
        // Guardar en localStorage
        const favorito = { grado, instituto, fecha: new Date().toISOString() };
        const favoritos = JSON.parse(localStorage.getItem('favoritos') || '[]');
        favoritos.push(favorito);
        localStorage.setItem('favoritos', JSON.stringify(favoritos));
    } else {
        button.innerHTML = '';
        console.log(`Grado desmarcado: ${grado} - ${instituto}`);
        // Eliminar de favoritos
        let favoritos = JSON.parse(localStorage.getItem('favoritos') || '[]');
        favoritos = favoritos.filter(f => !(f.grado === grado && f.instituto === instituto));
        localStorage.setItem('favoritos', JSON.stringify(favoritos));
    }
}

// Abrir enlace de salida profesional
function openCareerLink(career, type) {
    // URLs de ejemplo - aquí se pueden configurar las URLs reales
    const links = {
        'software': {
            'perfiles': 'https://www.todofp.es/dam/jcr:7534430f-60e5-4889-be4b-e3d446580c22/t-tulo-profesional-b-sico-en-electricidad-y-electr-n.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-6431'
        },
        'laboratorio': {
            'perfiles': 'https://www.todofp.es/dam/jcr:7534430f-60e5-4889-be4b-e3d446580c22/t-tulo-profesional-b-sico-en-electricidad-y-electr-n.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-6431'
        },
        'profesor': {
            'perfiles': 'https://www.todofp.es/dam/jcr:7534430f-60e5-4889-be4b-e3d446580c22/t-tulo-profesional-b-sico-en-electricidad-y-electr-n.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-6431'
        },
        'disenador': {
            'perfiles': 'https://www.todofp.es/dam/jcr:7534430f-60e5-4889-be4b-e3d446580c22/t-tulo-profesional-b-sico-en-electricidad-y-electr-n.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-6431'
        },
        'arquitecto': {
            'perfiles': 'https://www.todofp.es/dam/jcr:7534430f-60e5-4889-be4b-e3d446580c22/t-tulo-profesional-b-sico-en-electricidad-y-electr-n.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-6431'
        },
        'informatica1': {
            'perfiles': 'https://www.todofp.es/dam/jcr:d993b878-4231-4151-94cb-106a85c43e36/t-tulo-profesional-b-sico-en-inform-tica-de-oficina.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-9335'
        },
        'informatica2': {
            'perfiles': 'https://www.todofp.es/dam/jcr:d993b878-4231-4151-94cb-106a85c43e36/t-tulo-profesional-b-sico-en-inform-tica-de-oficina.pdf',
            'curriculo': 'http://boe.es/diario_boe/txt.php?id=BOE-A-2014-9335'
        }
    };
    
    const url = links[career][type];
    console.log(`Abriendo enlace: ${url}`);
    
    // Abrir en nueva ventana
    window.open(url, '_blank');
}

// ==================== FUNCIONES DEL PROFESOR ====================

// Función para cambiar de tab en el panel del profesor
function selectTabTeacher(tabName) {
    // Obtener todos los botones y paneles
    const tabButtons = document.querySelectorAll('#teacherIntegratedPanel .tab-button');
    const tabPanels = document.querySelectorAll('#teacherIntegratedPanel .tab-panel');
    
    // Remover clase active de todos los botones
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Ocultar todos los paneles
    tabPanels.forEach(panel => panel.style.display = 'none');
    
    // Activar el botón clickeado
    event.target.classList.add('active');
    
    // Mostrar el panel correspondiente
    if (tabName === 'perfil') {
        document.getElementById('teacherPerfilContent').style.display = 'block';
    } else if (tabName === 'contenido') {
        document.getElementById('teacherContenidoContent').style.display = 'block';
    } else if (tabName === 'seguimiento') {
        document.getElementById('teacherSeguimientoContent').style.display = 'block';
    }
}

// Cargar datos del profesor desde localStorage
function loadTeacherData() {
    // Cargar foto de perfil
    const savedPhoto = localStorage.getItem('teacher_profilePhoto');
    if (savedPhoto) {
        document.getElementById('teacher_profilePhoto').src = savedPhoto;
    }
    
    // Cargar nombre
    const savedNombre = localStorage.getItem('teacher_nombre');
    if (savedNombre) {
        document.getElementById('teacher_nombreValue').textContent = savedNombre;
    }
    
    // Cargar apellidos
    const savedApellidos = localStorage.getItem('teacher_apellidos');
    if (savedApellidos) {
        document.getElementById('teacher_apellidosValue').textContent = savedApellidos;
    }
    
    // Cargar localidad
    const savedLocalidad = localStorage.getItem('teacher_localidad');
    if (savedLocalidad) {
        document.getElementById('teacher_localidadValue').textContent = savedLocalidad;
    }
    
    // Cargar instituto
    const savedInstituto = localStorage.getItem('teacher_instituto');
    if (savedInstituto) {
        document.getElementById('teacher_institutoValue').textContent = savedInstituto;
    }
    
    // Cargar asignatura
    const savedAsignatura = localStorage.getItem('teacher_asignatura');
    if (savedAsignatura) {
        document.getElementById('teacher_asignaturaSelect').value = savedAsignatura;
    }
    
    // Cargar cursos
    const savedCursos = localStorage.getItem('teacher_cursos');
    if (savedCursos) {
        const cursos = JSON.parse(savedCursos);
        document.getElementById('curso_1eso').checked = cursos.includes('1º ESO');
        document.getElementById('curso_2eso').checked = cursos.includes('2º ESO');
        document.getElementById('curso_3eso').checked = cursos.includes('3º ESO');
        document.getElementById('curso_4eso').checked = cursos.includes('4º ESO');
    }
}

// Función para cargar datos del alumno (separada para claridad)
function loadStudentData() {
    // Cargar foto de perfil
    const savedPhoto = localStorage.getItem('profilePhoto');
    if (savedPhoto) {
        document.getElementById('profilePhoto').src = savedPhoto;
    }
    
    // Cargar nombre
    const savedNombre = localStorage.getItem('nombre');
    if (savedNombre) {
        document.getElementById('nombreValue').textContent = savedNombre;
    }
    
    // Cargar apellidos
    const savedApellidos = localStorage.getItem('apellidos');
    if (savedApellidos) {
        document.getElementById('apellidosValue').textContent = savedApellidos;
    }
    
    // Cargar localidad
    const savedLocalidad = localStorage.getItem('localidad');
    if (savedLocalidad) {
        document.getElementById('localidadValue').textContent = savedLocalidad;
    }
    
    // Cargar instituto
    const savedInstituto = localStorage.getItem('instituto');
    if (savedInstituto) {
        document.getElementById('institutoValue').textContent = savedInstituto;
    }
    
    // Cargar curso
    const savedCurso = localStorage.getItem('curso');
    if (savedCurso) {
        document.getElementById('cursoSelect').value = savedCurso;
    }
    
    // Cargar intereses
    const savedIntereses = localStorage.getItem('intereses');
    if (savedIntereses) {
        document.getElementById('interesesValue').textContent = savedIntereses;
    }
    
    // Cargar transporte
    const savedTransporte = localStorage.getItem('transporte');
    if (savedTransporte === 'true') {
        document.getElementById('transporteSwitch').checked = true;
        document.getElementById('transporteLabel').textContent = 'Sí';
    } else {
        document.getElementById('transporteSwitch').checked = false;
        document.getElementById('transporteLabel').textContent = 'No';
    }
}

// Abrir modal de edición para profesor
function openEditModalTeacher(field) {
    const modal = document.getElementById('editModal');
    const modalTitle = document.getElementById('modalFieldName');
    const modalInput = document.getElementById('modalInput');
    
    // Configurar el modal según el campo
    if (field === 'nombre') {
        modalTitle.textContent = 'Nombre';
        modalInput.value = document.getElementById('teacher_nombreValue').textContent;
    } else if (field === 'apellidos') {
        modalTitle.textContent = 'Apellidos';
        modalInput.value = document.getElementById('teacher_apellidosValue').textContent;
    } else if (field === 'localidad') {
        modalTitle.textContent = 'Localidad';
        modalInput.value = document.getElementById('teacher_localidadValue').textContent;
    } else if (field === 'instituto') {
        modalTitle.textContent = 'Instituto';
        modalInput.value = document.getElementById('teacher_institutoValue').textContent;
    }
    
    // Guardar el campo actual
    window.currentEditFieldTeacher = field;
    
    // Mostrar modal
    modal.style.display = 'block';
}

// Guardar campo editado del profesor
function saveFieldTeacher() {
    const field = window.currentEditFieldTeacher;
    const modalInput = document.getElementById('modalInput');
    const value = modalInput.value;
    
    // Actualizar el valor en la interfaz
    if (field === 'nombre') {
        document.getElementById('teacher_nombreValue').textContent = value;
        localStorage.setItem('teacher_nombre', value);
    } else if (field === 'apellidos') {
        document.getElementById('teacher_apellidosValue').textContent = value;
        localStorage.setItem('teacher_apellidos', value);
    } else if (field === 'localidad') {
        document.getElementById('teacher_localidadValue').textContent = value;
        localStorage.setItem('teacher_localidad', value);
    } else if (field === 'instituto') {
        document.getElementById('teacher_institutoValue').textContent = value;
        localStorage.setItem('teacher_instituto', value);
    }
    
    // Limpiar la variable
    window.currentEditFieldTeacher = null;
    
    // Cerrar modal
    closeEditModal();
}

// Cargar foto del profesor
function loadPhotoTeacher(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('teacher_profilePhoto').src = e.target.result;
            // Guardar en localStorage
            localStorage.setItem('teacher_profilePhoto', e.target.result);
        };
        reader.readAsDataURL(file);
    }
}

// Guardar asignatura del profesor
function saveAsignaturaTeacher() {
    const asignaturaSelect = document.getElementById('teacher_asignaturaSelect');
    localStorage.setItem('teacher_asignatura', asignaturaSelect.value);
}

// Guardar cursos seleccionados del profesor
function saveCursosTeacher() {
    const cursos = [];
    if (document.getElementById('curso_1eso').checked) cursos.push('1º ESO');
    if (document.getElementById('curso_2eso').checked) cursos.push('2º ESO');
    if (document.getElementById('curso_3eso').checked) cursos.push('3º ESO');
    if (document.getElementById('curso_4eso').checked) cursos.push('4º ESO');
    localStorage.setItem('teacher_cursos', JSON.stringify(cursos));
}

// Guardar perfil del profesor
function saveProfileTeacher() {
    // Guardar todos los campos
    localStorage.setItem('teacher_nombre', document.getElementById('teacher_nombreValue').textContent);
    localStorage.setItem('teacher_apellidos', document.getElementById('teacher_apellidosValue').textContent);
    localStorage.setItem('teacher_localidad', document.getElementById('teacher_localidadValue').textContent);
    localStorage.setItem('teacher_instituto', document.getElementById('teacher_institutoValue').textContent);
    localStorage.setItem('teacher_asignatura', document.getElementById('teacher_asignaturaSelect').value);
    
    // Guardar cursos seleccionados
    const cursos = [];
    if (document.getElementById('curso_1eso').checked) cursos.push('1º ESO');
    if (document.getElementById('curso_2eso').checked) cursos.push('2º ESO');
    if (document.getElementById('curso_3eso').checked) cursos.push('3º ESO');
    if (document.getElementById('curso_4eso').checked) cursos.push('4º ESO');
    localStorage.setItem('teacher_cursos', JSON.stringify(cursos));
    
    // Mostrar mensaje de confirmación
    alert('✅ Perfil guardado correctamente');
}

// Abrir asignatura del profesor
function openSubjectTeacher(subject) {
    alert('Funcionalidad de gestión de contenidos para profesores en desarrollo');
}

// Marcar ceros en rojo en la tabla de seguimiento
function markZerosInTable() {
    const rows = document.querySelectorAll('.seguimiento-table tbody tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td.stat-number');
        if (cells.length >= 6) {
            // Accesos (índice 0)
            if (cells[0].textContent.trim() === '0') {
                cells[0].classList.add('zero');
                // También marcar Resúmenes (índice 1) en rojo
                cells[1].classList.add('zero');
            }
            
            // Entregas (índice 2)
            const entregasValue = parseInt(cells[2].textContent.trim().split('/')[0]);
            if (entregasValue === 0) {
                cells[2].classList.add('zero');
                cells[3].classList.add('zero'); // Ayudas también en rojo
            } else if (entregasValue >= 1 && entregasValue <= 3) {
                cells[2].classList.add('orange');
                cells[3].classList.add('orange'); // Ayudas también en naranja
            }
            
            // Trabajos Monográficos (índice 4)
            const trabajosValue = parseInt(cells[4].textContent.trim().split('/')[0]);
            if (trabajosValue === 0) {
                cells[4].classList.add('zero');
            }
            
            // Score (índice 5)
            if (cells[5]) {
                const scoreValue = parseInt(cells[5].textContent.trim().replace('%', ''));
                if (scoreValue < 10) {
                    cells[5].classList.add('zero');
                } else if (scoreValue < 50) {
                    cells[5].classList.add('orange');
                }
            }
        }
    });
}

// Función para añadir una fila a la tabla de contenido
function addContentRow() {
    const unidad = document.getElementById('unidad-input').value.trim();
    const capitulo = document.getElementById('capitulo-input').value.trim();
    const descriptivo = document.getElementById('descriptivo-input').value.trim();
    const seccion = document.getElementById('seccion-input').value.trim();
    
    if (!capitulo || !descriptivo || !seccion) {
        alert('⚠️ Por favor, completa todos los campos (Capítulo, Descriptivo y Sección)');
        return;
    }
    
    const tableBody = document.getElementById('contentTableBody');
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td>${capitulo}</td>
        <td>${descriptivo}</td>
        <td>${seccion}</td>
        <td>
            <button class="btn-delete-row" onclick="deleteContentRow(this)">🗑️</button>
        </td>
    `;
    
    tableBody.appendChild(row);
    
    // Mostrar tabla y ocultar mensaje
    document.getElementById('contentTable').style.display = 'table';
    document.getElementById('emptyTableMessage').style.display = 'none';
    
    // Limpiar los campos
    document.getElementById('capitulo-input').value = '';
    document.getElementById('descriptivo-input').value = '';
    document.getElementById('seccion-input').value = '';
    
    // Guardar en localStorage
    saveContentData();
}

// Función para eliminar una fila
function deleteContentRow(button) {
    const row = button.closest('tr');
    row.remove();
    
    // Si no quedan filas, mostrar mensaje y ocultar tabla
    const tableBody = document.getElementById('contentTableBody');
    if (tableBody.querySelectorAll('tr').length === 0) {
        document.getElementById('contentTable').style.display = 'none';
        document.getElementById('emptyTableMessage').style.display = 'block';
    }
    
    saveContentData();
}

// Función para guardar los datos de contenido
function saveContentData() {
    const tableBody = document.getElementById('contentTableBody');
    const rows = tableBody.querySelectorAll('tr');
    const data = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        data.push({
            capitulo: cells[0].textContent,
            descriptivo: cells[1].textContent,
            seccion: cells[2].textContent
        });
    });
    
    localStorage.setItem('teacher_content', JSON.stringify(data));
}

// Función para cargar los datos de contenido
function loadContentData() {
    const data = localStorage.getItem('teacher_content');
    if (data) {
        const content = JSON.parse(data);
        const tableBody = document.getElementById('contentTableBody');
        
        if (content.length > 0) {
            document.getElementById('contentTable').style.display = 'table';
            document.getElementById('emptyTableMessage').style.display = 'none';
            
            content.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.capitulo}</td>
                    <td>${item.descriptivo}</td>
                    <td>${item.seccion}</td>
                    <td>
                        <button class="btn-delete-row" onclick="deleteContentRow(this)">🗑️</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    }
}

// Función para generar contenido
function generarContenido() {
    const unidad = document.getElementById('unidad-input').value.trim();
    const numEjercicios = document.getElementById('num-ejercicios-select').value;
    const trabajoMonografico = document.getElementById('monograficosSwitch').checked;
    
    if (!unidad) {
        alert('⚠️ Por favor, introduce el nombre de la UNIDAD antes de generar contenido');
        return;
    }
    
    // Aquí se implementará la lógica de generación de contenido
    console.log('Generando contenido para:', {
        unidad: unidad,
        numEjercicios: numEjercicios,
        trabajoMonografico: trabajoMonografico
    });
    
    alert(`✨ Generando contenido para la unidad: ${unidad}\n📝 Ejercicios: ${numEjercicios}\n📚 Trabajo monográfico: ${trabajoMonografico ? 'Sí' : 'No'}`);
}

// Función para manejar el switch de ejercicios monográficos
function toggleMonograficos() {
    const monograficosSwitch = document.getElementById('monograficosSwitch');
    const monograficosLabel = document.getElementById('monograficosLabel');
    
    if (monograficosSwitch.checked) {
        monograficosLabel.textContent = 'Sí';
        monograficosLabel.style.color = '#7EB900';
    } else {
        monograficosLabel.textContent = 'No';
        monograficosLabel.style.color = '#666';
    }
}

// Función para abrir un contenido generado
function abrirContenido(url) {
    window.open(url, '_blank');
}

// Función para eliminar un contenido generado
function eliminarContenidoGenerado(button) {
    const docItem = button.closest('.document-item');
    docItem.remove();
    saveContenidosGenerados();
}

// Guardar contenidos generados en localStorage
function saveContenidosGenerados() {
    const lista = document.getElementById('listaContenidosGenerados');
    const docItems = lista.querySelectorAll('.document-item');
    const contenidos = [];
    
    docItems.forEach(docItem => {
        const titulo = docItem.querySelector('.document-name').textContent;
        const viewBtn = docItem.querySelector('.btn-view');
        const url = viewBtn.getAttribute('onclick').match(/'([^']+)'/)[1];
        contenidos.push({ titulo, url });
    });
    
    localStorage.setItem('teacher_contenidos_generados', JSON.stringify(contenidos));
}

// Cargar contenidos generados desde localStorage
function loadContenidosGenerados() {
    const contenidos = JSON.parse(localStorage.getItem('teacher_contenidos_generados') || '[]');
    const lista = document.getElementById('listaContenidosGenerados');
    
    if (contenidos.length > 0) {
        lista.innerHTML = '';
        contenidos.forEach(contenido => {
            const docItem = document.createElement('div');
            docItem.className = 'document-item';
            docItem.innerHTML = `
                <div class="document-icon">📚</div>
                <div class="document-info">
                    <div class="document-name">${contenido.titulo}</div>
                    <div class="document-meta">PDF • 2.5 MB</div>
                </div>
                <div class="document-actions">
                    <button class="document-action-btn btn-view" onclick="abrirContenido('${contenido.url}')">
                        👁️ Visualizar
                    </button>
                    <button class="document-action-btn btn-delete" onclick="eliminarContenidoGenerado(this)">
                        🗑️ Eliminar
                    </button>
                </div>
            `;
            lista.appendChild(docItem);
        });
    }
}

// Llamar a la función cuando se carga el profesor
document.addEventListener('DOMContentLoaded', function() {
    // Entrar directamente al portal de alumno
    selectUser('alumno');
    
    // Cargar datos de contenido si existen
    loadContentData();
    loadContenidosGenerados();
    
    // Configurar el switch de monográficos
    const monograficosSwitch = document.getElementById('monograficosSwitch');
    if (monograficosSwitch) {
        monograficosSwitch.addEventListener('change', toggleMonograficos);
    }
    
    // Observar cuando se muestra la tabla de seguimiento
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.id === 'teacherSeguimientoContent' && 
                mutation.target.style.display !== 'none') {
                markZerosInTable();
            }
        });
    });
    
    const seguimientoTab = document.getElementById('teacherSeguimientoContent');
    if (seguimientoTab) {
        observer.observe(seguimientoTab, { attributes: true, attributeFilter: ['style'] });
    }
});
