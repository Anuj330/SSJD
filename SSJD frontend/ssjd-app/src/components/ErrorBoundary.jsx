import { Component } from 'react';

/**
 * Catches render/runtime errors in the tree below it and shows the message
 * instead of unmounting to a blank white screen.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Surface it in the console for debugging too.
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 p-6 dark:bg-gray-950">
          <div className="w-full max-w-lg rounded-2xl border border-red-200 bg-white p-6 shadow-sm dark:border-red-900/40 dark:bg-gray-900">
            <h1 className="text-lg font-bold text-red-600 dark:text-red-400">Something went wrong</h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              The page hit a runtime error. Details below:
            </p>
            <pre className="mt-4 max-h-64 overflow-auto rounded-lg bg-gray-100 p-3 text-xs text-red-700 dark:bg-gray-800 dark:text-red-300">
              {String(this.state.error?.stack || this.state.error)}
            </pre>
            <button
              onClick={() => window.location.assign('/')}
              className="mt-4 rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-700"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
