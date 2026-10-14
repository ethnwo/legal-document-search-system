import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://127.0.0.1:8000'

const EMPTY_FILTERS = {
  court: '',
  jurisdiction: '',
  start_date: '',
  end_date: '',
}

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedMethod, setSelectedMethod] = useState('hybrid')
  const [resultMethod, setResultMethod] = useState('hybrid')
  const [searchTimings, setSearchTimings] = useState(null)
  const [selectedCase, setSelectedCase] = useState(null)
  const [caseHtml, setCaseHtml] = useState('')
  const [caseLoading, setCaseLoading] = useState(false)
  const [caseError, setCaseError] = useState('')


  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [filterOptions, setFilterOptions] = useState({
    courts: [],
    jurisdictions: [],
  })
  const [filtersLoading, setFiltersLoading] = useState(true)

  // Load the available court and jurisdiction options from SQLite.
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/filters`)

        if (!response.ok) {
          throw new Error('Failed to load filter options')
        }

        const data = await response.json()
        setFilterOptions(data)
      } catch {
        setError('Unable to load filter options from the API.')
      } finally {
        setFiltersLoading(false)
      }
    }

    loadFilterOptions()
  }, [])

  const handleFilterChange = (event) => {
    const { name, value } = event.target

    setFilters((currentFilters) => ({
      ...currentFilters,
      [name]: value,
    }))
  }

  const handleSearch = async (selectedFilters = filters) => {
    if (!query.trim()) {
      setError('Please enter a search query first.')
      return
    }

    if (
      selectedFilters.start_date &&
      selectedFilters.end_date &&
      selectedFilters.start_date > selectedFilters.end_date
    ) {
      setError('The start date must be before or equal to the end date.')
      return
    }

    setSearchTimings(null)
    setLoading(true)
    setError('')

    try {
      const params = new URLSearchParams()
      params.set('query', query.trim())
      params.set('method', selectedMethod)

      Object.entries(selectedFilters).forEach(([key, value]) => {
        if (value) {
          params.set(key, value)
        }
      })

      const response = await fetch(
        `${API_BASE_URL}/search?${params.toString()}`
      )

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to fetch search results')
      }

      const data = await response.json()
      setResults(data.results)
      setResultMethod(data.method)
      setSearchTimings({
        retrieval: data.retrieval_time_ms,
        total: data.total_search_time_ms
      })
    } catch (err) {
      setError(err.message || 'Unable to connect to the search API.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    handleSearch()
  }

  const handleClearFilters = () => {
    setFilters(EMPTY_FILTERS)

    // If a query already exists, rerun it without metadata filters.
    if (query.trim()) {
      handleSearch(EMPTY_FILTERS)
    }
  }


const handleViewCase = async (result) => {
  setSelectedCase(result)
  setCaseHtml('')
  setCaseError('')
  setCaseLoading(true)

  try {
    const response = await fetch(
      `${API_BASE_URL}/cases/${encodeURIComponent(result.case_id)}/html`
    )

    if (!response.ok) {
      let message = 'Unable to load the full case.'

      try {
        const data = await response.json()
        message = data.detail || message
      } catch {
        // Keep the default error if the response isn't JSON.
      }

      throw new Error(message)
    }

    const html = await response.text()
    setCaseHtml(html)
  } catch (err) {
    setCaseError(err.message || 'Unable to connect to the case API.')
  } finally {
    setCaseLoading(false)
  }
}

const handleCloseCase = () => {
  setSelectedCase(null)
  setCaseHtml('')
  setCaseError('')
}


  return (
    <main className="app">
      <header className="header">
        <h1>Legal Document Search System</h1>
        <p>Search a collection of legal cases using lexical, semantic, or hybrid retrieval.</p>
      </header>

      <section className="search-section">
        <div className="retrieval-method-selector">
          <label htmlFor="retrieval-method">Retrieval Method</label>

          <select
            id="retrieval-method"
            value={selectedMethod}
            onChange={(event) => setSelectedMethod(event.target.value)}
            disabled={loading}
          >
            <option value="bm25">BM25 (Lexical)</option>
            <option value="semantic">Semantic Retrieval</option>
            <option value="hybrid">Hybrid (RRF)</option>
          </select>
        </div>
        <form className="search-bar" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Enter your legal query..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>

        <div className="filters-panel">
          <h2>Filter Results</h2>

          <div className="filters-grid">
            <div className="filter-field">
              <label htmlFor="court">Court</label>
              <select
                id="court"
                name="court"
                value={filters.court}
                onChange={handleFilterChange}
                disabled={filtersLoading}
              >
                <option value="">All courts</option>
                {filterOptions.courts.map((court) => (
                  <option key={court} value={court}>
                    {court}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="jurisdiction">Jurisdiction</label>
              <select
                id="jurisdiction"
                name="jurisdiction"
                value={filters.jurisdiction}
                onChange={handleFilterChange}
                disabled={filtersLoading}
              >
                <option value="">All jurisdictions</option>
                {filterOptions.jurisdictions.map((jurisdiction) => (
                  <option key={jurisdiction} value={jurisdiction}>
                    {jurisdiction}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-field">
              <label htmlFor="start_date">Decision date from</label>
              <input
                id="start_date"
                type="date"
                name="start_date"
                value={filters.start_date}
                onChange={handleFilterChange}
                max={filters.end_date || undefined}
              />
            </div>

            <div className="filter-field">
              <label htmlFor="end_date">Decision date to</label>
              <input
                id="end_date"
                type="date"
                name="end_date"
                value={filters.end_date}
                onChange={handleFilterChange}
                min={filters.start_date || undefined}
              />
            </div>
          </div>

          <div className="filter-actions">
            <button
              type="button"
              onClick={() => handleSearch()}
              disabled={loading || filtersLoading}
            >
              Apply Filters
            </button>

            <button
              type="button"
              className="clear-button"
              onClick={handleClearFilters}
              disabled={loading}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </section>

      <section className="results-section">
        {error && <p className="error">{error}</p>}

        {!loading && !error && results.length === 0 && (
          <p className="placeholder">
            Enter a query to search the legal case database.
          </p>
        )}

        {loading && <p className="placeholder">Searching for cases...</p>}

        {results.length > 0 && (
          <>
            <h2>Search Results ({results.length})</h2>

            {searchTimings && (
                <div className="search-timings">
                  <span>
                    Retrieval time: {searchTimings.retrieval.toFixed(3)} ms
                  </span>
                  <span>
                    Total backend search time: {searchTimings.total.toFixed(3)} ms
                  </span>
                </div>
            )}

            <div className="results">
              {results.map((result, index) => (
                <article className="result-card" key={result.case_id}>
                  <div className="result-rank">#{index + 1}</div>

                  <div className="result-content">
                    <h3>{result.case_name}</h3>

                    <p className="case-info">
                      {result.citation} - {result.decision_date}
                    </p>

                    <p className="case-court">
                      {result.court}
                    </p>

                    <div className="ranking-info">
                      {resultMethod === 'bm25' && (
                        <span>
                          BM25 Score: {result.score.toFixed(4)}
                        </span>
                      )}

                      {resultMethod === 'semantic' && (
                        <span>
                          Semantic Similarity: {result.score.toFixed(4)}
                        </span>
                      )}

                      {resultMethod === 'hybrid' && (
                        <>
                          <span>
                            RRF Score: {result.rrf_score.toFixed(6)}
                          </span>

                          <span>
                            BM25 Rank: #{result.bm25_rank ?? '-'}
                          </span>

                          <span>
                            Semantic Rank: #{result.semantic_rank ?? '-'}
                          </span>
                        </>
                      )}
                    </div>
                    <button
                      type="button"
                      className="view-case-button"
                      onClick={() => handleViewCase(result)}
                      disabled={caseLoading}
                    >
                      View Full Case
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
      {selectedCase && (
        <div
          className="case-modal-backdrop"
          onClick={handleCloseCase}
        >
          <section
            className="case-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="case-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="case-modal-header">
              <div>
                <h2 id="case-modal-title">
                  {selectedCase.case_name}
                </h2>
                <p>
                  {selectedCase.citation}
                  {selectedCase.decision_date
                    ? ` · ${selectedCase.decision_date}`
                    : ''}
                </p>
              </div>

              <button
                type="button"
                className="close-case-button"
                onClick={handleCloseCase}
                aria-label="Close full case"
              >
                &times;
              </button>
            </header>

            <div className="case-modal-content">
              {caseLoading && (
                <p className="placeholder">Loading full case...</p>
              )}

              {caseError && (
                <p className="error">{caseError}</p>
              )}

              {!caseLoading && !caseError && caseHtml && (
                <iframe
                  className="case-html-frame"
                  title={`Full text of ${selectedCase.case_name}`}
                  srcDoc={caseHtml}
                  sandbox=""
                />
              )}
            </div>
          </section>
        </div>
      )}
    </main>
  )
}

export default App