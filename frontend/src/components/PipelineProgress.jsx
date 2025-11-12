/**
 * PipelineProgress component for displaying real-time document processing progress.
 */

import React from 'react'
import './PipelineProgress.css'

export function PipelineProgress({ events }) {
  if (!events || events.length === 0) {
    return null
  }

  return (
    <div className="pipeline-progress">
      {events.map((event, idx) => (
        <div key={event.id || idx} className={`progress-step ${event.status}`}>
          {event.status === 'in_progress' && <span className="spinner"></span>}
          {event.status === 'completed' && <span className="check-mark">✓</span>}
          <span className="step-message">{event.message}</span>
        </div>
      ))}
    </div>
  )
}

export default PipelineProgress
