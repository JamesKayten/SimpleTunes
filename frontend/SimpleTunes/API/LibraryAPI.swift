import Foundation

// MARK: - Library & Stats API

extension APIService {
    
    func getStats() async throws -> LibraryStats {
        return try await get("/stats")
    }
    
    func scanLibrary(directory: String) async throws -> ScanResponse {
        return try await post("/library/scan", body: ["directory": directory])
    }
    
    func importFolder(path: String, createPlaylist: Bool = true, playlistName: String? = nil) async throws -> ImportResponse {
        var body: [String: Any] = ["folder_path": path, "create_playlist": createPlaylist]
        if let name = playlistName { body["playlist_name"] = name }
        return try await post("/library/import", body: body)
    }
    
    func getGenres() async throws -> [GenreCount] {
        struct Response: Decodable { let genres: [GenreCount] }
        let response: Response = try await get("/genres")
        return response.genres
    }
    
    func getYears() async throws -> [YearCount] {
        struct Response: Decodable { let years: [YearCount] }
        let response: Response = try await get("/years")
        return response.years
    }
    
    func getDecades() async throws -> [DecadeCount] {
        struct Response: Decodable { let decades: [DecadeCount] }
        let response: Response = try await get("/decades")
        return response.decades
    }
}

// MARK: - Response Types

struct GenreCount: Codable {
    let name: String
    let count: Int
}

struct YearCount: Codable {
    let year: Int
    let count: Int
}

struct DecadeCount: Codable {
    let decade: String
    let count: Int
}

struct ImportResponse: Codable {
    let collectionId: String
    let playlistId: String?
    let tracksAdded: Int
    let totalTracks: Int
}
