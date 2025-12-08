import Foundation

// MARK: - Playlist API

extension APIService {
    
    func getPlaylists() async throws -> [Playlist] {
        let r: PlaylistsResponse = try await get("/playlists")
        return r.playlists
    }
    
    func getPlaylist(id: String) async throws -> PlaylistDetail {
        return try await get("/playlists/\(id)")
    }
    
    func createPlaylist(name: String, description: String? = nil) async throws -> Playlist {
        var body: [String: Any] = ["name": name]
        if let d = description { body["description"] = d }
        return try await post("/playlists", body: body)
    }
    
    func updatePlaylist(id: String, name: String? = nil, description: String? = nil) async throws -> Playlist {
        var body: [String: Any] = [:]
        if let n = name { body["name"] = n }
        if let d = description { body["description"] = d }
        return try await put("/playlists/\(id)", body: body)
    }
    
    func deletePlaylist(id: String) async throws {
        try await delete("/playlists/\(id)")
    }
    
    func addTrackToPlaylist(playlistId: String, trackId: String, position: Int? = nil) async throws {
        var path = "/playlists/\(playlistId)/tracks/\(trackId)"
        if let p = position { path += "?position=\(p)" }
        let _: EmptyResponse = try await post(path, body: [:])
    }
    
    func removeTrackFromPlaylist(playlistId: String, trackId: String) async throws {
        try await delete("/playlists/\(playlistId)/tracks/\(trackId)")
    }
    
    func reorderPlaylist(playlistId: String, trackIds: [String]) async throws {
        let _: EmptyResponse = try await put("/playlists/\(playlistId)/reorder", body: ["track_ids": trackIds])
    }
    
    func createPlaylistFromFolder(path: String, name: String? = nil) async throws -> PlaylistFromFolderResponse {
        var body: [String: Any] = ["folder_path": path]
        if let n = name { body["name"] = n }
        return try await post("/playlists/from-folder", body: body)
    }
}

// MARK: - Response Types

struct PlaylistDetail: Codable {
    let id: String
    let name: String
    let description: String?
    let isSmart: Bool?
    let trackCount: Int?
    let totalDuration: Double?
    let coverPath: String?
    let createdAt: Date?
    let updatedAt: Date?
    let tracks: [Track]
}

struct PlaylistFromFolderResponse: Codable {
    let playlist: Playlist
    let tracksAdded: Int
}
