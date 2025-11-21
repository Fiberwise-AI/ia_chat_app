/**
 * SessionStats component for displaying session statistics (collapsible).
 */

import React, { useState } from 'react'

export function SessionStats({ messages }) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (messages.length === 0) return null

  const totalCost = messages
    .filter(m => m.metadata?.cost_usd)
    .reduce((sum, m) => sum + m.metadata.cost_usd, 0)

  const totalTokens = messages
    .filter(m => m.metadata?.tokens)
    .reduce((sum, m) => sum + m.metadata.tokens, 0)

  const assistantMessages = messages.filter(m => m.role === 'assistant').length
  const userMessages = messages.filter(m => m.role === 'user').length

  return (
    <div className="session-stats">
      <button
        className="stats-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        title="Show session statistics"
      >
        {isExpanded ? '▼' : '▶'} Session Stats
        {!isExpanded && (
          <span className="stats-preview">
            {userMessages + assistantMessages} messages · ${totalCost.toFixed(4)}
          </span>
        )}
      </button>
      {isExpanded && (
        <div className="stats-content">
          <span>User Messages: {userMessages}</span>
          <span>Assistant Messages: {assistantMessages}</span>
          <span>Total Tokens: {totalTokens.toLocaleString()}</span>
          <span>Total Cost: ${totalCost.toFixed(4)}</span>
        </div>
      )}
    </div>
  )
}

export default SessionStats
