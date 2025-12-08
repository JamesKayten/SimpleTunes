import Foundation

// MARK: - Core Models

struct Artist: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let sortName: String?
    let bio: String?
    let imagePath: String?
    let trackCount: Int?
    let albumCount: Int?

    enum CodingKeys: String, CodingKey {
        case id, name, bio
        case sortName = "sort_name"
        case imagePath = "image_path"
        case trackCount = "track_count"
        case albumCount = "album_count"
    }
}

struct Album: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let artistId: String?
    let artistName: String?
    let year: Int?
    let genre: String?
    let coverPath: String?
    let trackCount: Int?
    let totalTracks: Int?

    enum CodingKeys: String, CodingKey {
        case id, title, year, genre
        case artistId = "artist_id"
        case artistName = "artist_name"
        case coverPath = "cover_path"
        case trackCount = "track_count"
        case totalTracks = "total_tracks"
    }
}

struct Track: Codable, Identifiable, Hashable {
    let id: String
    let path: String
    let title: String
    let artistId: String?
    let artistName: String?
    let albumId: String?
    let albumName: String?
    let coverPath: String?
    let duration: Double?
    let trackNumber: Int?
    let discNumber: Int?
    let year: Int?
    let genre: String?
    let bitrate: Int?
    let sampleRate: Int?
    let fileFormat: String?
    let fileSize: Int?
    let playCount: Int?
    let lastPlayed: Date?
    let dateAdded: Date?
    let rating: Int?
    let favorite: Bool?
    let excluded: Bool?

    var artist: String { artistName ?? "Unknown Artist" }
    var album: String { albumName ?? "Unknown Album" }

    var durationFormatted: String {
        guard let dur = duration else { return "0:00" }
        let mins = Int(dur) / 60
        let secs = Int(dur) % 60
        return String(format: "%d:%02d", mins, secs)
    }

    enum CodingKeys: String, CodingKey {
        case id, path, title, duration, year, genre, bitrate, rating, favorite, excluded
        case artistId = "artist_id"
        case artistName = "artist_name"
        case albumId = "album_id"
        case albumName = "album_name"
        case coverPath = "cover_path"
        case trackNumber = "track_number"
        case discNumber = "disc_number"
        case sampleRate = "sample_rate"
        case fileFormat = "file_format"
        case fileSize = "file_size"
        case playCount = "play_count"
        case lastPlayed = "last_played"
        case dateAdded = "date_added"
    }
}

struct Playlist: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let description: String?
    let trackCount: Int?
    let totalDuration: Double?
    let createdAt: Date?
    let updatedAt: Date?

    enum CodingKeys: String, CodingKey {
        case id, name, description
        case trackCount = "track_count"
        case totalDuration = "total_duration"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    static func == (lhs: Playlist, rhs: Playlist) -> Bool { lhs.id == rhs.id }
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}
