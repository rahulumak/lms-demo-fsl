// ── SVG Icon library ──────────────────────────────────────────────────────────
export function Icon({ name, size = 18, color = 'currentColor', style = {} }) {
  const icons = {
    // lesson states
    check_circle: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><path d="M9 12l2 2 4-4" />
      </svg>
    ),
    circle: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
      </svg>
    ),
    play_circle: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><polygon points="10 8 16 12 10 16 10 8" fill={color} stroke="none" />
      </svg>
    ),
    // navigation / actions
    arrow_left: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 12H5M12 5l-7 7 7 7" />
      </svg>
    ),
    arrow_right: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 12h14M12 5l7 7-7 7" />
      </svg>
    ),
    // course / content
    book_open: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    ),
    graduation: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" />
      </svg>
    ),
    video: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="15" height="10" rx="2" /><polygon points="17 9 22 7 22 17 17 15" />
      </svg>
    ),
    // users / people
    users: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
    user: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
      </svg>
    ),
    // search / misc
    search: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
      </svg>
    ),
    inbox: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
        <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
      </svg>
    ),
    // password visibility
    eye: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
      </svg>
    ),
    eye_off: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
        <line x1="1" y1="1" x2="23" y2="23" />
      </svg>
    ),
    // logout / door
    log_out: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
      </svg>
    ),
    // image placeholder
    image: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
    ),
    // lesson draft
    file_text: (
      <svg viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', width: size, height: size, flexShrink: 0, ...style }}>
      {icons[name] ?? null}
    </span>
  )
}

// ── Components ────────────────────────────────────────────────────────────────

export function ProgressBar({ value }) {
  const pct = Math.min(100, Math.max(0, value || 0))
  return (
    <div className="progress-bar-wrap" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
      <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

export function Spinner() {
  return <div className="spinner" aria-label="Loading" />
}

export function ErrorMessage({ message }) {
  if (!message) return null
  return <div className="alert alert-error" role="alert">{message}</div>
}

export function EmptyState({ icon, title, message, action }) {
  return (
    <div className="empty-state">
      <span style={{ display: 'flex', justifyContent: 'center', color: 'var(--gray-400)', marginBottom: '.75rem' }}>
        {icon ? <Icon name={icon} size={48} /> : <Icon name="inbox" size={48} />}
      </span>
      <strong>{title}</strong>
      {message && <p>{message}</p>}
      {action}
    </div>
  )
}

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>
}

export function CourseCard({ course, footer }) {
  return (
    <div className="course-card">
      {/* Thumbnail with status badge pinned top-right */}
      <div className="course-card-thumb">
        {course.thumbnail_url
          ? <img src={course.thumbnail_url} alt={course.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : <Icon name="image" size={48} color="var(--primary)" />
        }
        {course.status && (
          <span className={`course-card-status-badge badge badge-${course.status}`}>{course.status}</span>
        )}
      </div>

      <div className="course-card-body">
        <div className="course-card-title">{course.title}</div>
        {course.short_description && (
          <div className="course-card-desc">{course.short_description}</div>
        )}
        {/* Footer: all buttons in one row */}
        <div className="course-card-footer">{footer}</div>
      </div>
    </div>
  )
}
