import Foundation

struct Track: Codable, Identifiable, Hashable {
    let id: String
    let path: String
    let title: String
    let artist: String
    let album: String
    let duration: Double
    
    var durationFormatted: String {
        let mins = Int(duration) / 60
        let secs = Int(duration) % 60
        return String(format: "%d:%02d", mins, secs)
    }
}

struct Playlist: Codable, Identifiable {
    let id: String
    let name: String
    let trackIds: [String]
    var tracks: [Track]?
    
    enum CodingKeys: String, CodingKey {
        case id, name, tracks
        case trackIds = "track_ids"
    }
}

struct TracksResponse: Codable {
    let tracks: [Track]
}

struct PlaylistsResponse: Codable {
    let playlists: [Playlist]
}

struct ScanResponse: Codable {
    let added: Int
    let total: Int
}
