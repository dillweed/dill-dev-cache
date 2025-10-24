# dill.dev/cache - Development Roadmap

This document tracks planned improvements and features for the multi-session encrypted scratch pad.

---

## 1. UI/UX Optimization

### 1.1 Simplify Session Interface
**Priority**: Medium | **Complexity**: Low | **Impact**: High  
**Status**: ✅ Completed 2025-10-24 — Header now groups the title, trims duplicate labels, streamlines the encryption key banner, and DOM order follows keyboard workflow: Back → Copy Key → Textarea → Save → Reload → Copy Content → Clear.

---

### 1.2 Enforce Actual Session Lock
**Priority**: High | **Complexity**: Medium | **Impact**: High  
**Status**: ✅ Completed 2025-10-24 — Lock overlay now clears the decrypted textarea, disables controls, hides the banner, and forces a encryption key re-entry before editing resumes.

**Notes:** The legacy behavior left decrypted content in the DOM. After the fix, inactivity triggers a full UI lock and wipes the key material; verify with manual idle tests on desktop and mobile.

---

### 1.3 Persistent Save Feedback
**Priority**: Medium | **Complexity**: Low | **Impact**: Medium  
**Status**: ✅ Completed 2025-10-24 — Status span now retains “Saved · HH:MM:SS” (or “Auto-saved…”) until the next action, giving continuous confirmation after manual or auto saves.

---

## 2. Client-Side Session Reset

### 2.1 Admin Session Reset Interface
**Priority**: High | **Complexity**: Medium | **Impact**: High  
**Status**: ✅ Completed 2025-10-24 — `/cache/admin.html` now provides a Basic-Auth-protected UI (user `cache-admin`) to list sessions, reset individually, or reset all; nginx restricts these endpoints and forwards to the existing Flask reset routes (`/api/cache/{id}/reset`, `/api/cache/reset-all`).

---

## 3. File Storage Support

### 3.1 Multi-Format Encrypted Storage
**Priority**: High | **Complexity**: Very High | **Impact**: Very High

Extend sessions to support file attachments alongside text content.

**High-Level Architecture:**

**Current System:**
```
Text Input → AES-GCM Encryption → Base64 Blob → JSON Storage
```

**Proposed System:**
```
Text + Files → Combined Package → AES-GCM Encryption → Base64 Blob → JSON Storage
               ↓
          [Metadata]
          - text: string
          - files: [
              {name: string, type: string, size: number, data: base64}
            ]
```

**Engineering Challenges:**

1. **Data Structure Design**
   - Package format before encryption
   - File metadata vs file data
   - Size limits per file and per session
   - MIME type handling

2. **Encryption Strategy**
   - Option A: Encrypt entire package (text + files) as single blob
   - Option B: Encrypt text and files separately, combine after
   - **Recommendation**: Option A for simplicity, maintains zero-knowledge

3. **Size Considerations**
   - Current: Text only, reasonable size
   - Proposed: Text + multiple files
   - Need maximum session size limit (suggest 10MB)
   - Warning UI when approaching limit
   - Consider chunking for large files

4. **Browser Performance**
   - File reading: `FileReader API`
   - Encryption of large binary data
   - Memory usage for multiple files
   - Progress indicators for large operations

**Frontend Implementation:**

**UI Components (session.html):**
- Drag-and-drop zone above text area
- File list display (name, size, type, remove button)
- Visual feedback during file processing
- Total size indicator
- "Drop files here or click to browse" interface

**File Handling:**
```javascript
// Pseudo-code structure
const sessionData = {
    text: "user text content",
    files: [
        {
            name: "document.pdf",
            type: "application/pdf",
            size: 524288,
            data: "base64encodeddata..."
        }
    ],
    version: "2.0"  // Format version
};

// Encrypt entire package
const encrypted = await encryptData(JSON.stringify(sessionData), encryption key);
```

**Drag-and-Drop UX:**
- Highlight drop zone on dragover
- Show file processing spinner
- Add files to list without removing existing
- Allow removing individual files before save
- Show total package size
- Warn if exceeding size limits

**Backend Changes (app.py):**

**Storage Format:**
```json
{
  "silver-lake": {
    "encrypted_content": "...larger base64 blob...",
    "salt": "silver-lake",
    "iv": "...",
    "updated": "2025-10-22T04:00:00.123456",
    "has_data": true,
    "content_type": "package",  // new field
    "size_bytes": 8388608       // new field
  }
}
```

**API Modifications:**
- `POST /api/cache/{session-id}` - Accept larger payloads
- Add size validation (reject if > 10MB)
- Update response to include size info
- Consider compression before encryption (gzip)

**Security Considerations:**
- File contents never transmitted unencrypted
- MIME type validation (prevent XSS via SVG, HTML)
- Filename sanitization
- No server-side file execution possible
- Same zero-knowledge guarantee maintained

**Download/Retrieval Flow:**
1. Decrypt session package
2. Parse JSON to get text + files array
3. Display text in textarea as before
4. Display file list with download buttons
5. For each file: create blob URL for download
6. Clean up blob URLs when done

**File Download UI:**
```
📎 Attached Files (3)
┌─────────────────────────────────────────┐
│ document.pdf         (512 KB)  [⬇ Save] │
│ screenshot.png       (1.2 MB)  [⬇ Save] │
│ config.json          (4 KB)    [⬇ Save] │
└─────────────────────────────────────────┘
```

**Implementation Phases:**

**Phase 1: Basic File Support**
- Single file upload (click to browse)
- Encrypt/decrypt single file + text
- Download encrypted file
- Size limit: 1MB

**Phase 2: Multi-File Support**
- Multiple file selection
- File list UI with remove option
- Increase limit to 5MB
- Better progress indicators

**Phase 3: Drag-and-Drop**
- Drag-and-drop interface
- Visual feedback
- Limit to 10MB
- Compression optimization

**Phase 4: Advanced Features**
- File preview (images, text)
- Inline image display option
- Zip multiple files on download
- Session size analytics

**Testing Requirements:**
- Test with various file types (PDF, images, text, binary)
- Test encryption/decryption performance with large files
- Test browser memory usage
- Test on mobile browsers
- Test error handling (corrupt files, size exceeded)
- Test backward compatibility (old text-only sessions)

**Backward Compatibility:**
- Old sessions (text-only) must still work
- Detect format version in decrypted data
- Graceful fallback if version 1.0 format
- No migration needed (lazy upgrade on save)

**Documentation Updates:**
- Update README with file storage info
- Document size limits
- Update use cases section
- Add file format specification
- Update troubleshooting for file issues

---

## 4. Additional Enhancement Ideas

### 4.1 Session Templates
**Priority**: Low | **Complexity**: Low

Pre-configured session templates for common use cases:
- Code snippet template (syntax highlighting note)
- Encryption Key template (structured fields)
- Command history template
- Quick note template

### 4.2 Dark Mode
**Priority**: Low | **Complexity**: Low

- Respect system preference (`prefers-color-scheme`)
- Optional manual toggle
- Save preference in localStorage

### 4.3 Session Naming
**Priority**: Low | **Complexity**: Medium

- Allow users to add custom labels to sessions
- Store in localStorage (not encrypted)
- Display alongside emoji name
- E.g., "🔵 Blue River - Project Alpha"

### 4.4 Export/Import Sessions
**Priority**: Medium | **Complexity**: Medium

- Export encrypted session to file
- Import from file to any session
- Useful for backup
- Maintains zero-knowledge (user keeps encryption key)

### 4.5 Mobile Optimization
**Priority**: Medium | **Complexity**: Medium

- Responsive design improvements
- Touch-friendly buttons
- Mobile keyboard optimization
- Consider progressive web app (PWA)

### 4.6 Session Search
**Priority**: Low | **Complexity**: High

- Search across all unlocked sessions
- Client-side only (maintains security)
- Requires unlocking sessions first
- Useful for finding forgotten notes

### 4.7 Rich Text Editing
**Priority**: Low | **Complexity**: High

- Optional Markdown preview
- Syntax highlighting for code
- Toggle between plain text and rich view
- Keep encryption unchanged

### 4.8 Session Expiry
**Priority**: Low | **Complexity**: Medium

- Optional auto-delete after X days
- User configurable per session
- Warning before deletion
- Reduces stale data accumulation

---

## 5. Security & Reliability Hardening

### 5.1 Strengthen Session Encryption Key Entropy
**Priority**: High | **Complexity**: Low | **Impact**: High  
**Status**: ✅ Completed 2025-10-24 — Encryption Keys now append two random words from a 64-word list plus a 5-digit code (≈40 bits of entropy) while preserving the friendly session-name prefix.

---

### 5.2 Use Per-Session PBKDF2 Salts
**Priority**: High | **Complexity**: Medium | **Impact**: High  
**Status**: ✅ Completed 2025-10-24 — The backend now issues a random 16-byte (hex) salt per session and serves it via the API; the client persists and reuses that salt for key derivation while retaining legacy support.

---

### 5.3 Prevent Concurrent Cache File Corruption
**Priority**: Medium | **Complexity**: Low | **Impact**: Medium  
**Status**: ✅ Completed 2025-10-24 — `load_cache()` now uses a shared `flock`, and `save_cache()` writes through an exclusive lock with fsync to avoid clobbering `cache_data.json` during concurrent saves.

---

### 5.4 Clean Legacy Keys from `cache_data.json`
**Priority**: Low | **Complexity**: Low | **Impact**: Low  
**Status**: ✅ Completed 2025-10-24 — `load_cache()` now normalizes the JSON on read, dropping non-session keys and backfilling missing fields before persisting.

---

## 6. Tooling Maintenance

### 6.1 Fix Reset Script SyntaxError
**Priority**: High | **Complexity**: Low | **Impact**: Medium
**Status**: ✅ Completed 2025-10-24 — Quoting fixed in `reset_cache_session.py`; script runs cleanly (`python3 reset_cache_session.py blue-river`) and resets via SSH as documented.

## Notes

**Development Principles:**
- Maintain zero-dependency philosophy
- Keep codebase auditable (< 2000 lines total)
- Preserve zero-knowledge security model
- Ensure backward compatibility
- Prioritize keyboard navigation
- Mobile-friendly where possible

**Testing Strategy:**
- Manual testing on Chrome, Firefox, Safari
- Keyboard-only navigation testing
- Mobile device testing (iOS, Android)
- Large file encryption performance testing
- Cross-device workflow testing

**Deployment Checklist:**
- Test on staging environment first
- Backup cache_data.json before changes
- Monitor logs after deployment
- Verify encryption/decryption working
- Test rollback procedure

---

**Last Updated**: 2025-10-22
**Version**: 1.0
