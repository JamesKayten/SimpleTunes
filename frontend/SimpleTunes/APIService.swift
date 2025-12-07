import Foundation

actor APIService {
    static let shared = APIService()
    private let baseURL = "http://127.0.0.1:8000"
    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()
    
    func getLibrary() async throws -> [Track] {
        let response: TracksResponse = try await get("/library")
        return response.tracks
    }
    
    func scanLibrary(directory: String) async throws -> ScanResponse {
        return try await post("/library/scan", body: ["directory": directory])
    }
    
    func searchTracks(query: String) async throws -> [Track] {
        let response: TracksResponse = try await get("/library/search/\(query)")
        return response.tracks
    }
    
    func getPlaylists() async throws -> [Playlist] {
        let response: PlaylistsResponse = try await get("/playlists")
        return response.playlists
    }
    
    func createPlaylist(name: String) async throws -> Playlist {
        return try await post("/playlists", body: ["name": name, "track_ids": []])
    }
    
    private func get<T: Decodable>(_ path: String) async throws -> T {
        let url = URL(string: baseURL + path)!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try decoder.decode(T.self, from: data)
    }
    
    private func post<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        var request = URLRequest(url: URL(string: baseURL + path)!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, _) = try await URLSession.shared.data(for: request)
        return try decoder.decode(T.self, from: data)
    }
}
