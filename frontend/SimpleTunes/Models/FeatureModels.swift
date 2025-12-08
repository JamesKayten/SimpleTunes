import Foundation

// MARK: - Lyrics

struct LyricLine: Codable {
    let time: Double
    let text: String
}

struct Lyrics: Codable {
    let trackId: String
    let plainLyrics: String?
    let syncedLyrics: String?
    let source: String?
    let isSynced: Bool
    var parsedLines: [LyricLine]?

    enum CodingKeys: String, CodingKey {
        case source
        case trackId = "track_id"
        case plainLyrics = "plain_lyrics"
        case syncedLyrics = "synced_lyrics"
        case isSynced = "is_synced"
        case parsedLines = "parsed_lines"
    }
}

// MARK: - Audio Analysis

struct AudioAnalysis: Codable {
    let trackId: String
    let trackGain: Double?
    let trackPeak: Double?
    let albumGain: Double?
    let albumPeak: Double?
    let encoderDelay: Int?
    let encoderPadding: Int?
    let totalSamples: Int?
    let bpm: Double?
    let analyzedAt: Date?

    enum CodingKeys: String, CodingKey {
        case bpm
        case trackId = "track_id"
        case trackGain = "track_gain"
        case trackPeak = "track_peak"
        case albumGain = "album_gain"
        case albumPeak = "album_peak"
        case encoderDelay = "encoder_delay"
        case encoderPadding = "encoder_padding"
        case totalSamples = "total_samples"
        case analyzedAt = "analyzed_at"
    }
}

// MARK: - Tag Editing

struct TagInfo: Codable {
    let trackId: String
    let path: String
    let fileFormat: String?
    let fileTags: FileTags?
    let databaseTags: FileTags?
    let synced: Bool

    enum CodingKeys: String, CodingKey {
        case path, synced
        case trackId = "track_id"
        case fileFormat = "file_format"
        case fileTags = "file_tags"
        case databaseTags = "database_tags"
    }
}

struct FileTags: Codable {
    let title: String?
    let artist: String?
    let album: String?
    let genre: String?
    let year: Int?
    let trackNumber: Int?
    let discNumber: Int?
    let albumArtist: String?
    let composer: String?
    let comment: String?

    enum CodingKeys: String, CodingKey {
        case title, artist, album, genre, year, composer, comment
        case trackNumber = "track_number"
        case discNumber = "disc_number"
        case albumArtist = "album_artist"
    }
}

struct TagUpdateRequest: Codable {
    var title: String?
    var artist: String?
    var album: String?
    var genre: String?
    var year: Int?
    var trackNumber: Int?
    var discNumber: Int?
    var albumArtist: String?
    var composer: String?
    var writeToFile: Bool = true

    enum CodingKeys: String, CodingKey {
        case title, artist, album, genre, year, composer
        case trackNumber = "track_number"
        case discNumber = "disc_number"
        case albumArtist = "album_artist"
        case writeToFile = "write_to_file"
    }
}

// MARK: - Watch Folders

struct WatchFolder: Codable, Identifiable {
    let id: String
    let path: String
    let isActive: Bool
    let autoImport: Bool
    let watchSubdirs: Bool
    let lastEvent: Date?
    let createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case id, path
        case isActive = "is_active"
        case autoImport = "auto_import"
        case watchSubdirs = "watch_subdirs"
        case lastEvent = "last_event"
        case createdAt = "created_at"
    }
}

// MARK: - Export

enum PlaylistExportFormat: String, Codable, CaseIterable {
    case m3u = "m3u"
    case m3u8 = "m3u8"
    case pls = "pls"
    case xspf = "xspf"
    case json = "json"
}

struct ExportResult: Codable {
    let success: Bool
    let path: String?
    let format: String?
    let trackCount: Int?
    let error: String?

    enum CodingKeys: String, CodingKey {
        case success, path, format, error
        case trackCount = "track_count"
    }
}
