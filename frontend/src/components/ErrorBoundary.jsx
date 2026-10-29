import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('Render error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '1rem', padding: '2rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem' }}>⚠️</div>
          <h2>Something went wrong</h2>
          <p style={{ color: 'var(--gray-600)', maxWidth: 400 }}>
            An unexpected error occurred. Please refresh the page or go back to the dashboard.
          </p>
          <div style={{ display: 'flex', gap: '.75rem' }}>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>Refresh Page</button>
            <button className="btn btn-secondary" onClick={() => { this.setState({ hasError: false }); window.history.back() }}>Go Back</button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
