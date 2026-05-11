chunk.content  = H3 heading + prose paragraph(s)
chunk.metadata = {
    code_example,
    parameter_table,
    parent_section (H2),
    doc_title,
    endpoint + method,
    chunk_type,
    source_url / file,
    version
}

{
  // derived from file path
  version:        "v2",
  doc_category:   "users",

  // derived from markdown structure  
  doc_title:      "Users API",
  parent_section: "Endpoints",
  section:        "Create User",

  // derived from content (regex/parsing)
  endpoint:       "POST /users",
  chunk_type:     "endpoint",  // endpoint | concept | error | guide

  // stored, not embedded
  code_example:   "...",
  parameter_table: "...",

  // for attribution + re-indexing
  source_url:     "/docs/v2/users#create-user",
  source_file:    "docs/v2/users.md",
  created_at:     "2024-11-01",
  updated_at:     "2025-01-10",
  chunk_id:       "v2-users-create-001"
}