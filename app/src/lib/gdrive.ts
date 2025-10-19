/**
 * Minimal Google Drive API v3 wrapper using fetch.
 * This module avoids SDKs and expects OAuth token provided by caller.
 * Never hardcode secrets. Use environment variables only in the app shell.
 */

export interface DriveListParams {
  q?: string
  pageSize?: number
  fields?: string
}

export interface DriveFile {
  id: string
  name: string
  mimeType: string
}

const DRIVE_V3 = 'https://www.googleapis.com/drive/v3'
const UPLOAD_V3 = 'https://www.googleapis.com/upload/drive/v3'

export function setBearer(token: string) {
  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }
}

export async function listFiles(token: string, params: DriveListParams = {}): Promise<DriveFile[]> {
  const url = new URL(`${DRIVE_V3}/files`)
  const search = new URLSearchParams()
  if (params.q) search.set('q', params.q)
  search.set('pageSize', String(params.pageSize ?? 100))
  search.set('fields', params.fields ?? 'files(id,name,mimeType)')
  url.search = search.toString()

  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Drive list failed: ${res.status}`)
  const data = (await res.json()) as { files: DriveFile[] }
  return data.files
}

export async function createFolder(token: string, name: string, parentId?: string): Promise<DriveFile> {
  const body = {
    name,
    mimeType: 'application/vnd.google-apps.folder',
    ...(parentId ? { parents: [parentId] } : {}),
  }
  const res = await fetch(`${DRIVE_V3}/files`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Drive create folder failed: ${res.status}`)
  return (await res.json()) as DriveFile
}

export async function uploadJson(
  token: string,
  name: string,
  json: unknown,
  parentId?: string,
): Promise<DriveFile> {
  const metadata = {
    name,
    mimeType: 'application/json',
    ...(parentId ? { parents: [parentId] } : {}),
  }
  const boundary = '-------icudystonia-' + Math.random().toString(36).slice(2)
  const body = `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(
    metadata,
  )}\r\n--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${JSON.stringify(json)}\r\n--${boundary}--`

  const res = await fetch(`${UPLOAD_V3}/files?uploadType=multipart`, {
    method: 'POST',
    headers: {
      'Content-Type': `multipart/related; boundary=${boundary}`,
      Authorization: `Bearer ${token}`,
    },
    body,
  })
  if (!res.ok) throw new Error(`Drive upload failed: ${res.status}`)
  return (await res.json()) as DriveFile
}
