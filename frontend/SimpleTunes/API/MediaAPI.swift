import Foundation

// MARK: - Scrobbling API

extension APIService {
    
    func getScrobbleConfigs() async throws -> [ScrobbleConfigInfo] {
        struct R: Decodable { let configs: [ScrobbleConfigInfo] }
        let r: R = try await get("/scrobble/config")
        return r.configs
    }
    
    func scrobbleTrack(trackId: String, timestamp: Int? = nil) async throws {
        var path = "/scrobble/\(trackId)"
        if let ts = timestamp { path += "?timestamp=\(ts)" }
        let _: EmptyResponse = try await post(path, body: [:])
    }
    
    func updateNowPlaying(trackId: String) async throws {
        let _: EmptyResponse = try await post("/scrobble/\(trackId)/now-playing", body: [:])
    }
}

// MARK: - Lyrics API

extension APIService {
    
    func getLyrics(trackId: String) async throws -> Lyrics {
        return try await get("/lyrics/\(trackId)")
    }
    
    func fetchLyrics(trackId: String) async throws -> Lyrics {
        return try await post("/lyrics/\(trackId)/fetch", body: [:])
    }
}

// MARK: - Audio Analysis API

extension APIService {
    
    func getAudioAnalysis(trackId: String) async throws -> AudioAnalysis {
        return try await get("/analysis/\(trackId)")
    }
    
    func analyzeTrack(trackId: String) async throws -> AudioAnalysis {
        return try await post("/analysis/\(trackId)", body: [:])
    }
}

// MARK: - Tags API

extension APIService {
    
    func getTrackTags(trackId: String) async throws -> TagInfo {
        return try await get("/tags/\(trackId)")
    }
    
    func updateTrackTags(trackId: String, tags: TagUpdateRequest) async throws -> TagInfo {
        let data = try encoder.encode(tags)
        let body = try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
        return try await put("/tags/\(trackId)", body: body)
    }
}

// MARK: - Watch Folders API

extension APIService {
    
    func getWatchFolders() async throws -> [WatchFolder] {
        let r: WatchFoldersResponse = try await get("/watch/folders")
        return r.folders
    }
    
    func addWatchFolder(path: String, autoImport: Bool = true) async throws -> WatchFolder {
        return try await post("/watch/folders", body: ["path": path, "auto_import": autoImport])
    }
    
    func removeWatchFolder(id: String) async throws {
        try await delete("/watch/folders/\(id)")
    }
}

// MARK: - Export API

extension APIService {
    
    func exportPlaylist(playlistId: String, format: PlaylistExportFormat = .m3u, relativePaths: Bool = false) async throws -> ExportResult {
        return try await post("/export/playlist/\(playlistId)", body: ["format": format.rawValue, "relative_paths": relativePaths])
    }
}

// MARK: - Artwork & Streaming

extension APIService {
    
    func fetchAlbumArtwork(albumId: String) async throws -> String? {
        struct R: Decodable { let path: String? }
        let r: R = try await post("/artwork/album/\(albumId)", body: [:])
        return r.path
    }
    
    func fetchArtistArtwork(artistId: String) async throws -> String? {
        struct R: Decodable { let path: String? }
        let r: R = try await post("/artwork/artist/\(artistId)", body: [:])
        return r.path
    }
    
    func artworkURL(filename: String) -> URL? {
        URL(string: "\(baseURL)/artwork/\(filename)")
    }
    
    func streamURL(trackId: String) -> URL? {
        URL(string: "\(baseURL)/stream/\(trackId)")
    }
}

// MARK: - Response Types

struct ScrobbleConfigInfo: Codable {
    let service: String
    let enabled: Bool
    let username: String?
}
