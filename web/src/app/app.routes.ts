import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'ask' },
  {
    path: 'ask',
    title: 'Ask · Research Engine',
    loadComponent: () => import('./pages/ask/ask-page').then((m) => m.AskPage),
  },
  {
    path: 'library',
    title: 'Library · Research Engine',
    loadComponent: () => import('./pages/library/library-page').then((m) => m.LibraryPage),
  },
  {
    path: 'benchmarks',
    title: 'Benchmarks · Research Engine',
    loadComponent: () => import('./pages/benchmarks/benchmarks-page').then((m) => m.BenchmarksPage),
  },
  {
    path: '**',
    title: 'Not found · Research Engine',
    loadComponent: () => import('./pages/not-found/not-found-page').then((m) => m.NotFoundPage),
  },
];
