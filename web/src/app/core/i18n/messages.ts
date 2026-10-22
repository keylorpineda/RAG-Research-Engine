export const EN = {
  nav: { label: 'Main', ask: 'Ask', library: 'Library', benchmarks: 'Benchmarks' },
  language: { label: 'Language' },
  theme: { toLight: 'Switch to light theme', toDark: 'Switch to dark theme' },
  footer: { label: 'Footer', license: 'MIT license' },
  ask: { title: 'Ask your documents' },
  library: { title: 'Library' },
  benchmarks: { title: 'Benchmarks' },
  notFound: { title: 'Page not found', back: 'Back to Ask' },
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
  library: { title: 'Biblioteca' },
  benchmarks: { title: 'Benchmarks' },
  notFound: { title: 'Página no encontrada', back: 'Volver a Preguntar' },
  errors: {
    network:
      'No se puede conectar con la API. Puede estar despertando: intenta de nuevo en un minuto.',
    unknown: 'Algo salió mal.',
  },
};
