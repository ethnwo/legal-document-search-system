import { useState } from 'react'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async () => {
    if (!query.trim()) {
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`http://127.0.0.1:8000/search?query=${encodeURIComponent(query)}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch search results')
      }

      const data = await response.json()
      setResults(data.results)
    } catch (err) {
      setError('Unable to connect to the search API.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <main className="app">
      <header className="header">
        <h1>Legal Document Search System</h1>
        <p>Search a collection of legal cases using hybrid retrieval.</p>
      </header>

      <section className="search-selection">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Enter your legal query..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={handleKeyDown}
          />

          <button onClick={handleSearch} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </section>

      <section className="results-section">
        {error && <p className="error">{error}</p>}

        {!loading && !error && results.length === 0 && (
          <p className="placeholder">
            Enter a query to search the legal case database.
          </p>
        )}

        {results.length > 0 && (
          <>
            <h2>Search Results</h2>
            <div className="results">
              {results.map((result, index) => (
                <article className="result-card" key={result.case_id}>
                  <div className="result-rank">
                    #{index + 1}
                  </div>

                  <div className="result-content">
                    <h3>{result.case_name}</h3>

                    <p className="case-info">
                      {result.citation} - {result.decision_date}
                    </p>

                    <p className="case-court">
                      {result.court}
                    </p>

                    <div className="ranking-info">
                      <span>
                        RRF Score: {result.rrf_score.toFixed(6)}
                      </span>

                      <span>
                        BM25 Rank: #{result.bm25_rank ?? '-'}
                      </span>

                      <span>
                        Semantic Rank: #{result.semantic_rank ?? '-'}
                      </span>
                    </div>
                  </div>
                </article>
              ))}
            </div>  
          </>
        )}
      </section>
    </main>
  )
}

export default App