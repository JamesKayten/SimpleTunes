import Foundation

// MARK: - API Response Models

struct TracksResponse: Codable {
    let tracks: [Track]
    let total: Int?
    let page: Int?
    let pageSize: Int?

    enum CodingKeys: String, CodingKey {
        case tracks, total, page
        case pageSize = "page_size"
    }
}

struct PlaylistsResponse: Codable {
    let playlists: [Playlist]
}

struct ArtistsResponse: Codable {
    let artists: [Artist]
}

struct AlbumsResponse: Codable {
    let albums: [Album]
}

struct ScanResponse: Codable {
    let added: Int
    let updated: Int?
    let total: Int
    let errors: [String]?
}

struct WatchFoldersResponse: Codable {
    let folders: [WatchFolder]
}

// MARK: - Statistics

struct LibraryStats: Codable {
    let totalTracks: Int
    let totalAlbums: Int
    let totalArtists: Int
    let totalPlaylists: Int?
    let totalCollections: Int?
    let totalDurationHours: Double?

    enum CodingKeys: String, CodingKey {
        case totalTracks = "total_tracks"
        case totalAlbums = "total_albums"
        case totalArtists = "total_artists"
        case totalPlaylists = "total_playlists"
        case totalCollections = "total_collections"
        case totalDurationHours = "total_duration_hours"
    }

    var totalDurationFormatted: String {
        guard let hours = totalDurationHours else { return "0h" }
        if hours >= 1 { return String(format: "%.0fh", hours) }
        return String(format: "%.0fm", hours * 60)
    }
}
