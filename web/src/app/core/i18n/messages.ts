/**
 * UI copy. `{name}` placeholders are filled by I18nService.format; ES must have the same keys
 * (a spec checks it).
 */
export const EN = {
  nav: { label: 'Main', ask: 'Ask', library: 'Library', benchmarks: 'Benchmarks' },
  language: { label: 'Language' },
  theme: { toLight: 'Switch to light theme', toDark: 'Switch to dark theme' },
  footer: { label: 'Footer', license: 'MIT license' },
  ask: { title: 'Ask your documents' },
  library: {
    title: 'Library',
    stats: '{docs} documents · {passages} passages',
    drop: 'Drop files here',
    release: 'Release to upload',
    browse: 'Browse',
    accepted: 'PDF, MD, TXT · up to {mb} MB',
    filter: 'Filter documents',
    tabs: { all: 'All', ready: 'Ready', working: 'In progress', error: 'Failed' },
    passages: '{n} passages',
    status: {
      uploading: 'Uploading {pct}',
      PENDING: 'Queued',
      PROCESSING: 'Processing',
      READY: 'Ready',
      ERROR: 'Failed',
    },
    retry: 'Retry',
    retryLabel: 'Process {name} again',
    deleteLabel: 'Delete {name}',
    deleted: '{name} deleted',
    undo: 'Undo',
    dismiss: 'Dismiss',
    emptyTitle: 'No documents yet',
    emptyBody:
      'Add a PDF, Markdown or text file. It is split into passages and indexed for search.',
    emptyFilter: 'Nothing here with this filter.',
    loadError: 'The library could not be loaded.',
    tryAgain: 'Try again',
    rejected: {
      type: '{name}: only PDF, MD and TXT files are accepted.',
      size: '{name} is larger than {mb} MB.',
      empty: '{name} is empty.',
      count: 'Upload at most {max} files at a time.',
    },
    uploadsOff: 'Uploads are turned off in this demo. Ask about the documents already here.',
  },
  benchmarks: { title: 'Benchmarks' },
  notFound: { title: 'Page not found', back: 'Back to Ask' },
  time: { now: 'just now' },
  art: {
    emptyLibrary: 'An empty stack of documents',
    pipeline: 'A document split into passages and turned into vectors',
    retrieval: 'Passages ranked for the question',
    noEvidence: 'A search that found nothing above the threshold',
  },
  errors: {
    network: 'The API cannot be reached. It may be waking up: try again in a minute.',
    unknown: 'Something went wrong.',
  },
};

export type Messages = typeof EN;

export const ES: Messages = {
  nav: { label: 'Principal', ask: 'Preguntar', library: 'Biblioteca', benchmarks: 'Benchmarks' },
  language: { label: 'Idioma' },
  theme: { toLight: 'Cambiar a tema claro', toDark: 'Cambiar a tema oscuro' },
  footer: { label: 'Pie de página', license: 'Licencia MIT' },
  ask: { title: 'Pregunta a tus documentos' },
  library: {
    title: 'Biblioteca',
    stats: '{docs} documentos · {passages} pasajes',
    drop: 'Suelta archivos aquí',
    release: 'Suelta para subir',
    browse: 'Elegir',
    accepted: 'PDF, MD, TXT · hasta {mb} MB',
    filter: 'Filtrar documentos',
    tabs: { all: 'Todos', ready: 'Listos', working: 'En proceso', error: 'Con error' },
    passages: '{n} pasajes',
    status: {
      uploading: 'Subiendo {pct}',
      PENDING: 'En cola',
      PROCESSING: 'Procesando',
      READY: 'Listo',
      ERROR: 'Con error',
    },
    retry: 'Reintentar',
    retryLabel: 'Procesar {name} de nuevo',
    deleteLabel: 'Eliminar {name}',
    deleted: '{name} eliminado',
    undo: 'Deshacer',
    dismiss: 'Cerrar',
    emptyTitle: 'Aún no hay documentos',
    emptyBody: 'Agrega un PDF, Markdown o texto. Se divide en pasajes y se indexa para buscar.',
    emptyFilter: 'No hay nada con este filtro.',
    loadError: 'No se pudo cargar la biblioteca.',
    tryAgain: 'Intentar de nuevo',
    rejected: {
      type: '{name}: solo se aceptan archivos PDF, MD y TXT.',
      size: '{name} pesa más de {mb} MB.',
      empty: '{name} está vacío.',
      count: 'Sube como máximo {max} archivos a la vez.',
    },
    uploadsOff:
      'La subida de archivos está desactivada en esta demo. Pregunta sobre los documentos que ya están.',
  },
  benchmarks: { title: 'Benchmarks' },
  notFound: { title: 'Página no encontrada', back: 'Volver a Preguntar' },
  time: { now: 'ahora' },
  art: {
    emptyLibrary: 'Una pila de documentos vacía',
    pipeline: 'Un documento dividido en pasajes y convertido en vectores',
    retrieval: 'Pasajes ordenados para la pregunta',
    noEvidence: 'Una búsqueda que no encontró nada sobre el umbral',
  },
  errors: {
    network:
      'No se puede conectar con la API. Puede estar despertando: intenta de nuevo en un minuto.',
    unknown: 'Algo salió mal.',
  },
};
