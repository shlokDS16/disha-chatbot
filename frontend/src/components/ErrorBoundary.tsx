import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info);
  }

  reset = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    if (this.props.fallback) return this.props.fallback(error, this.reset);

    return (
      <div className="p-6 max-w-md mx-auto mt-10">
        <div className="card p-5">
          <div className="text-rose-700 dark:text-rose-400 font-semibold mb-1">
            Something broke while rendering.
          </div>
          <p className="text-sm text-ink-soft dark:text-slate-300 mb-3 break-words">
            {error.message || "Unknown error."}
          </p>
          <button className="btn-primary" onClick={this.reset}>
            Try again
          </button>
        </div>
      </div>
    );
  }
}
