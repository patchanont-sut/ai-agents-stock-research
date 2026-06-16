// MarketMind AI Dashboard — Error Boundary
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] Caught render error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="card card-error error-boundary-card">
          <div className="error-boundary-icon">⚠</div>
          <h2 className="error-boundary-title">
            Something went wrong while rendering this analysis.
          </h2>
          <p className="error-boundary-message">
            {this.state.error?.message || 'Unknown render error'}
          </p>
          <button className="btn btn-primary error-boundary-reload" onClick={this.handleReload}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}