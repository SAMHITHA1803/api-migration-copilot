"use client";

import { useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [library, setLibrary] = useState("pandas");
  const [versionRange, setVersionRange] = useState("1.x->2.x");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const [selectedFile, setSelectedFile] = useState(0);
  const [showPatch, setShowPatch] = useState(false);

  async function analyzeRepository() {
    setLoading(true);
    setError("");
    setResult(null);
    setSelectedFile(0);
    setShowPatch(false);

    try {
      const response = await fetch(
        `${API_URL}/migrate-repository`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            repo_url: repoUrl,
            library,
            version_range: versionRange,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error ||
            `Request failed with status ${response.status}`
        );
      }

      if (!data.success) {
        throw new Error(
          data.error ||
            data.agent_summary ||
            "Migration could not be completed."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err?.message ||
          "Something went wrong while running the migration."
      );
    } finally {
      setLoading(false);
    }
  }

  const results = result?.results || [];

  const git = result?.git || {};

  const totalFindings = results.reduce(
    (total, item) =>
      total + (item?.findings?.length || 0),
    0
  );

  const filesWithFindings = results.filter(
    (item) =>
      item?.findings &&
      item.findings.length > 0
  ).length;

  const selectedResult =
    results[selectedFile] || null;

  const toolTrace = result?.tool_trace || [];

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#0b1020",
        color: "#f8fafc",
        padding: "40px 24px",
        fontFamily:
          "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <section
          style={{
            marginBottom: "32px",
          }}
        >
          <div
            style={{
              fontSize: "13px",
              fontWeight: 700,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              marginBottom: "10px",
              opacity: 0.65,
            }}
          >
            Developer Tool
          </div>

          <h1
            style={{
              fontSize: "42px",
              lineHeight: 1.1,
              margin: 0,
              fontWeight: 800,
            }}
          >
            API Migration Copilot
          </h1>

          <p
            style={{
              maxWidth: "760px",
              color: "#94a3b8",
              fontSize: "16px",
              lineHeight: 1.7,
              marginTop: "14px",
            }}
          >
            Detect deprecated APIs, retrieve migration
            documentation, generate verified code changes,
            and create a GitHub pull request.
          </p>
        </section>

        {/* ================================================= */}
        {/* INPUT CARD */}
        {/* ================================================= */}

        <section
          style={{
            background: "#111827",
            border: "1px solid #263247",
            borderRadius: "16px",
            padding: "24px",
            marginBottom: "28px",
          }}
        >
          <label
            style={{
              display: "block",
              fontSize: "13px",
              fontWeight: 700,
              marginBottom: "8px",
            }}
          >
            GitHub Repository
          </label>

          <input
            value={repoUrl}
            onChange={(e) =>
              setRepoUrl(e.target.value)
            }
            placeholder="https://github.com/username/repository"
            disabled={loading}
            style={{
              width: "100%",
              boxSizing: "border-box",
              background: "#0b1020",
              color: "#f8fafc",
              border: "1px solid #334155",
              borderRadius: "10px",
              padding: "13px 14px",
              outline: "none",
              marginBottom: "18px",
            }}
          />

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "1fr 1fr",
              gap: "16px",
            }}
          >
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "13px",
                  fontWeight: 700,
                  marginBottom: "8px",
                }}
              >
                Library
              </label>

              <select
                value={library}
                onChange={(e) =>
                  setLibrary(e.target.value)
                }
                disabled={loading}
                style={{
                  width: "100%",
                  background: "#0b1020",
                  color: "#f8fafc",
                  border: "1px solid #334155",
                  borderRadius: "10px",
                  padding: "13px 14px",
                }}
              >
                <option value="pandas">
                  pandas
                </option>
              </select>
            </div>

            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "13px",
                  fontWeight: 700,
                  marginBottom: "8px",
                }}
              >
                Migration
              </label>

              <select
                value={versionRange}
                onChange={(e) =>
                  setVersionRange(
                    e.target.value
                  )
                }
                disabled={loading}
                style={{
                  width: "100%",
                  background: "#0b1020",
                  color: "#f8fafc",
                  border: "1px solid #334155",
                  borderRadius: "10px",
                  padding: "13px 14px",
                }}
              >
                <option value="1.x->2.x">
                  pandas 1.x → 2.x
                </option>
              </select>
            </div>
          </div>

          <button
            onClick={analyzeRepository}
            disabled={
              loading ||
              !repoUrl.trim()
            }
            style={{
              marginTop: "20px",
              width: "100%",
              padding: "14px",
              borderRadius: "10px",
              border: "none",
              background:
                loading ||
                !repoUrl.trim()
                  ? "#334155"
                  : "#f8fafc",
              color:
                loading ||
                !repoUrl.trim()
                  ? "#94a3b8"
                  : "#0b1020",
              fontWeight: 800,
              cursor:
                loading ||
                !repoUrl.trim()
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {loading
              ? "Running Migration Agent..."
              : "Analyze Repository"}
          </button>
        </section>

        {/* ================================================= */}
        {/* ERROR */}
        {/* ================================================= */}

        {error && (
          <section
            style={{
              background: "#2a1115",
              border: "1px solid #7f1d1d",
              borderRadius: "14px",
              padding: "18px",
              marginBottom: "28px",
            }}
          >
            <div
              style={{
                fontWeight: 800,
                marginBottom: "6px",
              }}
            >
              Migration failed
            </div>

            <div
              style={{
                color: "#fecaca",
                whiteSpace: "pre-wrap",
                lineHeight: 1.6,
              }}
            >
              {error}
            </div>
          </section>
        )}

        {/* ================================================= */}
        {/* LOADING */}
        {/* ================================================= */}

        {loading && (
          <section
            style={{
              background: "#111827",
              border: "1px solid #263247",
              borderRadius: "16px",
              padding: "24px",
              marginBottom: "28px",
            }}
          >
            <div
              style={{
                fontWeight: 800,
                marginBottom: "8px",
              }}
            >
              Migration agent is running
            </div>

            <div
              style={{
                color: "#94a3b8",
                lineHeight: 1.6,
              }}
            >
              The agent is cloning the repository,
              analyzing Python files, retrieving migration
              documentation, generating changes, verifying
              them, and preparing the Git workflow.
            </div>
          </section>
        )}

        {/* ================================================= */}
        {/* RESULTS */}
        {/* ================================================= */}

        {result && (
          <>
            {/* --------------------------------------------- */}
            {/* SUMMARY CARDS */}
            {/* --------------------------------------------- */}

            <section
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(4, 1fr)",
                gap: "14px",
                marginBottom: "28px",
              }}
            >
              <StatCard
                label="Files Scanned"
                value={
                  result.files_scanned ??
                  0
                }
              />

              <StatCard
                label="Files With Findings"
                value={
                  filesWithFindings
                }
              />

              <StatCard
                label="Deprecated APIs"
                value={
                  totalFindings
                }
              />

              <StatCard
                label="Migration Status"
                value={
                  result.success
                    ? "Completed"
                    : "Failed"
                }
              />
            </section>

            {/* --------------------------------------------- */}
            {/* REPOSITORY */}
            {/* --------------------------------------------- */}

            <section
              style={{
                background: "#111827",
                border: "1px solid #263247",
                borderRadius: "16px",
                padding: "22px",
                marginBottom: "28px",
              }}
            >
              <SectionTitle>
                Repository
              </SectionTitle>

              <div
                style={{
                  color: "#cbd5e1",
                  wordBreak: "break-all",
                }}
              >
                {result.repository}
              </div>

              {result.local_path && (
                <div
                  style={{
                    marginTop: "8px",
                    color: "#64748b",
                    fontSize: "13px",
                    wordBreak:
                      "break-all",
                  }}
                >
                  Local workspace:{" "}
                  {result.local_path}
                </div>
              )}
            </section>

            {/* --------------------------------------------- */}
            {/* FINDINGS */}
            {/* --------------------------------------------- */}

            <section
              style={{
                background: "#111827",
                border: "1px solid #263247",
                borderRadius: "16px",
                padding: "22px",
                marginBottom: "28px",
              }}
            >
              <SectionTitle>
                Migration Findings
              </SectionTitle>

              {results.length === 0 ? (
                <div
                  style={{
                    color: "#94a3b8",
                  }}
                >
                  No deprecated APIs were detected.
                </div>
              ) : (
                results.map(
                  (item, fileIndex) => (
                    <div
                      key={`finding-file-${fileIndex}`}
                      style={{
                        marginBottom:
                          fileIndex ===
                          results.length - 1
                            ? 0
                            : "20px",
                        paddingBottom:
                          fileIndex ===
                          results.length - 1
                            ? 0
                            : "20px",
                        borderBottom:
                          fileIndex ===
                          results.length - 1
                            ? "none"
                            : "1px solid #263247",
                      }}
                    >
                      <div
                        style={{
                          fontWeight: 800,
                          marginBottom:
                            "12px",
                        }}
                      >
                        File {fileIndex + 1}
                      </div>

                      {item.findings?.map(
                        (
                          finding,
                          findingIndex
                        ) => (
                          <div
                            key={`finding-${fileIndex}-${findingIndex}`}
                            style={{
                              background:
                                "#0b1020",
                              border:
                                "1px solid #263247",
                              borderRadius:
                                "10px",
                              padding:
                                "14px",
                              marginBottom:
                                "10px",
                            }}
                          >
                            <div
                              style={{
                                display:
                                  "flex",
                                justifyContent:
                                  "space-between",
                                gap: "12px",
                                marginBottom:
                                  "8px",
                              }}
                            >
                              <strong>
                                {finding.api}
                              </strong>

                              <span
                                style={{
                                  fontSize:
                                    "11px",
                                  fontWeight:
                                    800,
                                  textTransform:
                                    "uppercase",
                                  opacity:
                                    0.7,
                                }}
                              >
                                {
                                  finding.severity
                                }
                              </span>
                            </div>

                            <div
                              style={{
                                color:
                                  "#94a3b8",
                                fontSize:
                                  "14px",
                                lineHeight:
                                  1.5,
                              }}
                            >
                              Line{" "}
                              {
                                finding.line
                              }
                              {" · "}
                              {
                                finding.message
                              }
                            </div>

                            <div
                              style={{
                                marginTop:
                                  "8px",
                                color:
                                  "#cbd5e1",
                                fontSize:
                                  "14px",
                              }}
                            >
                              Replacement:{" "}
                              <strong>
                                {
                                  finding.replacement
                                }
                              </strong>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  )
                )
              )}
            </section>

            {/* --------------------------------------------- */}
            {/* FILE RESULTS */}
            {/* --------------------------------------------- */}

            {results.length > 0 && (
              <section
                style={{
                  background: "#111827",
                  border:
                    "1px solid #263247",
                  borderRadius: "16px",
                  padding: "22px",
                  marginBottom: "28px",
                }}
              >
                <SectionTitle>
                  Migration Results
                </SectionTitle>

                {/* File tabs */}

                <div
                  style={{
                    display: "flex",
                    gap: "8px",
                    flexWrap: "wrap",
                    marginBottom:
                      "20px",
                  }}
                >
                  {results.map(
                    (item, index) => (
                      <button
                        key={`file-tab-${index}`}
                        onClick={() =>
                          setSelectedFile(
                            index
                          )
                        }
                        style={{
                          background:
                            selectedFile ===
                            index
                              ? "#f8fafc"
                              : "#0b1020",
                          color:
                            selectedFile ===
                            index
                              ? "#0b1020"
                              : "#cbd5e1",
                          border:
                            "1px solid #334155",
                          borderRadius:
                            "8px",
                          padding:
                            "9px 12px",
                          cursor:
                            "pointer",
                          fontWeight:
                            700,
                        }}
                      >
                        File {index + 1}
                      </button>
                    )
                  )}
                </div>

                {selectedResult && (
                  <>
                    {/* Findings */}

                    <div
                      style={{
                        marginBottom:
                          "24px",
                      }}
                    >
                      <h3
                        style={{
                          margin:
                            "0 0 12px",
                          fontSize:
                            "16px",
                        }}
                      >
                        Detected APIs
                      </h3>

                      {selectedResult.findings?.map(
                        (
                          finding,
                          index
                        ) => (
                          <div
                            key={`selected-finding-${index}`}
                            style={{
                              padding:
                                "10px 12px",
                              background:
                                "#0b1020",
                              border:
                                "1px solid #263247",
                              borderRadius:
                                "8px",
                              marginBottom:
                                "8px",
                            }}
                          >
                            <strong>
                              {
                                finding.api
                              }
                            </strong>

                            {" → "}

                            {
                              finding.replacement
                            }
                          </div>
                        )
                      )}
                    </div>

                    {/* Migration Guidance */}

                    {selectedResult.migration_guidance
                      ?.length > 0 && (
                      <div
                        style={{
                          marginBottom:
                            "24px",
                        }}
                      >
                        <h3
                          style={{
                            margin:
                              "0 0 12px",
                            fontSize:
                              "16px",
                          }}
                        >
                          Retrieved Migration
                          Documentation
                        </h3>

                        {selectedResult.migration_guidance.map(
                          (
                            guidance,
                            index
                          ) => (
                            <div
                              key={`guidance-${index}`}
                              style={{
                                background:
                                  "#0b1020",
                                border:
                                  "1px solid #263247",
                                borderRadius:
                                  "10px",
                                padding:
                                  "14px",
                                marginBottom:
                                  "10px",
                              }}
                            >
                              <div
                                style={{
                                  fontWeight:
                                    800,
                                  marginBottom:
                                    "8px",
                                }}
                              >
                                {
                                  guidance.api
                                }
                              </div>

                              <pre
                                style={{
                                  whiteSpace:
                                    "pre-wrap",
                                  color:
                                    "#94a3b8",
                                  fontSize:
                                    "12px",
                                  lineHeight:
                                    1.6,
                                  margin: 0,
                                }}
                              >
                                {
                                  guidance.documentation
                                }
                              </pre>
                            </div>
                          )
                        )}
                      </div>
                    )}

                    {/* Code comparison */}

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns:
                          "1fr 1fr",
                        gap: "16px",
                        marginBottom:
                          "24px",
                      }}
                    >
                      <CodePanel
                        title="Original Code"
                        code={
                          selectedResult.original_code ||
                          "Original code unavailable."
                        }
                      />

                      <CodePanel
                        title="Migrated Code"
                        code={
                          selectedResult.migrated_code ||
                          "Migrated code unavailable."
                        }
                      />
                    </div>

                    {/* Verification */}

                    {selectedResult.verification && (
                      <div
                        style={{
                          background:
                            selectedResult
                              .verification
                              .valid
                              ? "#102318"
                              : "#2a1115",
                          border:
                            `1px solid ${
                              selectedResult
                                .verification
                                .valid
                                ? "#28543a"
                                : "#7f1d1d"
                            }`,
                          borderRadius:
                            "10px",
                          padding:
                            "16px",
                          marginBottom:
                            "20px",
                        }}
                      >
                        <div
                          style={{
                            fontWeight:
                              800,
                            marginBottom:
                              "6px",
                          }}
                        >
                          Verification{" "}
                          {selectedResult
                            .verification
                            .valid
                            ? "Passed"
                            : "Failed"}
                        </div>

                        <div
                          style={{
                            color:
                              "#94a3b8",
                            lineHeight:
                              1.5,
                          }}
                        >
                          {
                            selectedResult
                              .verification
                              .message
                          }
                        </div>
                      </div>
                    )}

                    {/* Patch */}

                    {selectedResult.patch && (
                      <div>
                        <button
                          onClick={() =>
                            setShowPatch(
                              !showPatch
                            )
                          }
                          style={{
                            background:
                              "#0b1020",
                            color:
                              "#f8fafc",
                            border:
                              "1px solid #334155",
                            borderRadius:
                              "8px",
                            padding:
                              "10px 14px",
                            cursor:
                              "pointer",
                            fontWeight:
                              700,
                          }}
                        >
                          {showPatch
                            ? "Hide Patch"
                            : "Show Patch"}
                        </button>

                        {showPatch && (
                          <pre
                            style={{
                              marginTop:
                                "14px",
                              background:
                                "#020617",
                              border:
                                "1px solid #263247",
                              borderRadius:
                                "10px",
                              padding:
                                "16px",
                              overflowX:
                                "auto",
                              color:
                                "#cbd5e1",
                              fontSize:
                                "12px",
                              lineHeight:
                                1.6,
                            }}
                          >
                            {
                              selectedResult
                                .patch
                                .patch
                            }
                          </pre>
                        )}
                      </div>
                    )}
                  </>
                )}
              </section>
            )}

            {/* --------------------------------------------- */}
            {/* AGENT ACTIVITY */}
            {/* --------------------------------------------- */}

            {toolTrace.length > 0 && (
              <section
                style={{
                  background: "#111827",
                  border:
                    "1px solid #263247",
                  borderRadius: "16px",
                  padding: "22px",
                  marginBottom: "28px",
                }}
              >
                <SectionTitle>
                  Agent Activity
                </SectionTitle>

                <div>
                  {toolTrace.map(
                    (trace, index) => {
                      const success =
                        trace?.result
                          ?.success;

                      return (
                        <div
                          key={`trace-${index}`}
                          style={{
                            display:
                              "flex",
                            alignItems:
                              "center",
                            gap: "12px",
                            padding:
                              "10px 0",
                            borderBottom:
                              index ===
                              toolTrace.length -
                                1
                                ? "none"
                                : "1px solid #1e293b",
                          }}
                        >
                          <div
                            style={{
                              width:
                                "8px",
                              height:
                                "8px",
                              borderRadius:
                                "50%",
                              background:
                                success
                                  ? "#4ade80"
                                  : "#f59e0b",
                              flexShrink: 0,
                            }}
                          />

                          <div
                            style={{
                              fontFamily:
                                "monospace",
                              fontSize:
                                "13px",
                              color:
                                "#cbd5e1",
                            }}
                          >
                            {trace.tool}
                          </div>

                          <div
                            style={{
                              marginLeft:
                                "auto",
                              fontSize:
                                "11px",
                              color:
                                "#64748b",
                            }}
                          >
                            {success
                              ? "success"
                              : "completed"}
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              </section>
            )}

            {/* --------------------------------------------- */}
            {/* GIT WORKFLOW */}
            {/* --------------------------------------------- */}

            <section
              style={{
                background: "#111827",
                border:
                  "1px solid #263247",
                borderRadius: "16px",
                padding: "22px",
                marginBottom: "28px",
              }}
            >
              <SectionTitle>
                Git Workflow
              </SectionTitle>

              <GitStatus
                label="Migration Branch"
                value={
                  git.branch_name ||
                  "Not created"
                }
                success={
                  git.branch_created
                }
              />

              <GitStatus
                label="Commit"
                value={
                  git.commit_hash
                    ? git.commit_hash.slice(
                        0,
                        12
                      )
                    : "Not created"
                }
                success={
                  git.commit_created
                }
              />

              <GitStatus
                label="Push"
                value={
                  git.push_succeeded
                    ? "Pushed successfully"
                    : "Not pushed"
                }
                success={
                  git.push_succeeded
                }
              />

              <GitStatus
                label="Pull Request"
                value={
                  git.pull_request_created
                    ? "Created"
                    : "Not created"
                }
                success={
                  git.pull_request_created
                }
              />

              {git.pull_request_url && (
                <a
                  href={
                    git.pull_request_url
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display:
                      "inline-block",
                    marginTop:
                      "16px",
                    color:
                      "#f8fafc",
                    fontWeight:
                      800,
                    textDecoration:
                      "underline",
                  }}
                >
                  Open Pull Request →
                </a>
              )}
            </section>

            {/* --------------------------------------------- */}
            {/* AGENT SUMMARY */}
            {/* --------------------------------------------- */}

            {result.agent_summary && (
              <section
                style={{
                  background: "#111827",
                  border:
                    "1px solid #263247",
                  borderRadius: "16px",
                  padding: "22px",
                }}
              >
                <SectionTitle>
                  Agent Summary
                </SectionTitle>

                <div
                  style={{
                    color: "#cbd5e1",
                    lineHeight: 1.7,
                    whiteSpace:
                      "pre-wrap",
                  }}
                >
                  {result.agent_summary}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}


/* ========================================================= */
/* COMPONENTS */
/* ========================================================= */

function SectionTitle({ children }) {
  return (
    <h2
      style={{
        fontSize: "18px",
        margin: "0 0 18px",
        fontWeight: 800,
      }}
    >
      {children}
    </h2>
  );
}


function StatCard({
  label,
  value,
}) {
  return (
    <div
      style={{
        background: "#111827",
        border: "1px solid #263247",
        borderRadius: "14px",
        padding: "18px",
      }}
    >
      <div
        style={{
          color: "#64748b",
          fontSize: "12px",
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.05em",
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: "24px",
          fontWeight: 800,
          marginTop: "8px",
        }}
      >
        {value}
      </div>
    </div>
  );
}


function CodePanel({
  title,
  code,
}) {
  return (
    <div>
      <h3
        style={{
          fontSize: "15px",
          margin: "0 0 10px",
        }}
      >
        {title}
      </h3>

      <pre
        style={{
          margin: 0,
          background: "#020617",
          border: "1px solid #263247",
          borderRadius: "10px",
          padding: "16px",
          overflowX: "auto",
          minHeight: "220px",
          color: "#cbd5e1",
          fontSize: "12px",
          lineHeight: 1.6,
        }}
      >
        {code}
      </pre>
    </div>
  );
}


function GitStatus({
  label,
  value,
  success,
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "12px 0",
        borderBottom:
          "1px solid #1e293b",
      }}
    >
      <div
        style={{
          width: "9px",
          height: "9px",
          borderRadius: "50%",
          background: success
            ? "#4ade80"
            : "#475569",
          flexShrink: 0,
        }}
      />

      <div
        style={{
          fontWeight: 700,
          minWidth: "150px",
        }}
      >
        {label}
      </div>

      <div
        style={{
          color: success
            ? "#cbd5e1"
            : "#64748b",
          fontFamily:
            "monospace",
          fontSize: "13px",
          wordBreak:
            "break-all",
        }}
      >
        {value}
      </div>
    </div>
  );
}