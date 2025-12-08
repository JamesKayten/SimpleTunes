import Foundation

// MARK: - Queue Models

enum RepeatMode: String, Codable, CaseIterable {
    case off = "off"
    case one = "one"
    case all = "all"
}

struct QueueItem: Codable, Identifiable {
    let id: String
    let trackId: String
    let position: Int
    let addedAt: Date?
    var track: Track?

    enum CodingKeys: String, CodingKey {
        case id, position, track
        case trackId = "track_id"
        case addedAt = "added_at"
    }
}

struct QueueState: Codable {
    let currentTrackId: String?
    let currentPosition: Int
    let isShuffled: Bool
    let repeatMode: RepeatMode
    let originalOrder: [String]?
    var items: [QueueItem]?
    var currentTrack: Track?

    enum CodingKeys: String, CodingKey {
        case items
        case currentTrackId = "current_track_id"
        case currentPosition = "current_position"
        case isShuffled = "is_shuffled"
        case repeatMode = "repeat_mode"
        case originalOrder = "original_order"
        case currentTrack = "current_track"
    }
}

// MARK: - Sorting & Filtering

enum SortField: String, Codable, CaseIterable {
    case title = "title"
    case artist = "artist"
    case album = "album"
    case year = "year"
    case genre = "genre"
    case duration = "duration"
    case playCount = "play_count"
    case lastPlayed = "last_played"
    case rating = "rating"
    case dateAdded = "date_added"
    case trackNumber = "track_number"

    var displayName: String {
        switch self {
        case .title: return "Title"
        case .artist: return "Artist"
        case .album: return "Album"
        case .year: return "Year"
        case .genre: return "Genre"
        case .duration: return "Duration"
        case .playCount: return "Play Count"
        case .lastPlayed: return "Last Played"
        case .rating: return "Rating"
        case .dateAdded: return "Date Added"
        case .trackNumber: return "Track Number"
        }
    }
}

enum SortOrder: String, Codable, CaseIterable {
    case asc = "asc"
    case desc = "desc"
}
