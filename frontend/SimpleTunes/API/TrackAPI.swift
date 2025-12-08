import Foundation

// MARK: - Track API

extension APIService {
    
    func getTracks(
        search: String? = nil, genre: String? = nil, artistId: String? = nil,
        albumId: String? = nil, yearFrom: Int? = nil, yearTo: Int? = nil,
        ratingMin: Int? = nil, favoritesOnly: Bool = false, excludeRemoved: Bool = true,
        sortBy: SortField = .title, sortOrder: SortOrder = .asc,
        limit: Int = 100, offset: Int = 0
    ) async throws -> TracksResponse {
        var params: [String] = []
        if let s = search { params.append("search=\(s.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? s)") }
        if let g = genre { params.append("genre=\(g)") }
        if let a = artistId { params.append("artist_id=\(a)") }
        if let a = albumId { params.append("album_id=\(a)") }
        if let y = yearFrom { params.append("year_from=\(y)") }
        if let y = yearTo { params.append("year_to=\(y)") }
        if let r = ratingMin { params.append("rating_min=\(r)") }
        if favoritesOnly { params.append("favorites_only=true") }
        if !excludeRemoved { params.append("exclude_removed=false") }
        params.append("sort_by=\(sortBy.rawValue)")
        params.append("sort_order=\(sortOrder.rawValue)")
        params.append("limit=\(limit)")
        params.append("offset=\(offset)")
        return try await get("/tracks?\(params.joined(separator: "&"))")
    }
    
    func getTrack(id: String) async throws -> Track {
        return try await get("/tracks/\(id)")
    }
    
    func recordPlay(trackId: String) async throws -> Int {
        struct R: Decodable { let playCount: Int }
        let r: R = try await post("/tracks/\(trackId)/play", body: [:])
        return r.playCount
    }
    
    func getRecentlyPlayed(limit: Int = 50) async throws -> [Track] {
        let r: TracksResponse = try await get("/tracks/recent/played?limit=\(limit)")
        return r.tracks
    }
    
    func getRecentlyAdded(limit: Int = 50) async throws -> [Track] {
        let r: TracksResponse = try await get("/tracks/recent/added?limit=\(limit)")
        return r.tracks
    }
    
    func getMostPlayed(limit: Int = 50) async throws -> [Track] {
        let r: TracksResponse = try await get("/tracks/top/played?limit=\(limit)")
        return r.tracks
    }
    
    func getTopRated(limit: Int = 50) async throws -> [Track] {
        let r: TracksResponse = try await get("/tracks/top/rated?limit=\(limit)")
        return r.tracks
    }
    
    func getFavorites() async throws -> [Track] {
        let r: TracksResponse = try await get("/tracks/favorites")
        return r.tracks
    }
    
    func getExcluded() async throws -> [Track] {
        let r: TracksResponse = try await get("/tracks/excluded")
        return r.tracks
    }
    
    // MARK: - Ratings
    
    func updateRating(trackId: String, rating: Int? = nil, favorite: Bool? = nil, excluded: Bool? = nil, notes: String? = nil) async throws -> RatingResponse {
        var body: [String: Any] = [:]
        if let r = rating { body["rating"] = r }
        if let f = favorite { body["favorite"] = f }
        if let e = excluded { body["excluded"] = e }
        if let n = notes { body["notes"] = n }
        return try await put("/tracks/\(trackId)/rating", body: body)
    }
    
    func setFavorite(trackId: String, favorite: Bool) async throws -> RatingResponse {
        return try await updateRating(trackId: trackId, favorite: favorite)
    }
    
    func setRating(trackId: String, rating: Int) async throws -> RatingResponse {
        return try await updateRating(trackId: trackId, rating: rating)
    }
    
    // MARK: - Albums
    
    func getAlbums(artistId: String? = nil, genre: String? = nil, year: Int? = nil, sortBy: String = "title", sortOrder: String = "asc") async throws -> [Album] {
        var params = ["sort_by=\(sortBy)", "sort_order=\(sortOrder)"]
        if let a = artistId { params.append("artist_id=\(a)") }
        if let g = genre { params.append("genre=\(g)") }
        if let y = year { params.append("year=\(y)") }
        let r: AlbumsResponse = try await get("/albums?\(params.joined(separator: "&"))")
        return r.albums
    }
    
    func getAlbum(id: String) async throws -> AlbumDetail {
        return try await get("/albums/\(id)")
    }
    
    // MARK: - Artists
    
    func getArtists(sortBy: String = "name") async throws -> [Artist] {
        let r: ArtistsResponse = try await get("/artists?sort_by=\(sortBy)")
        return r.artists
    }
    
    func getArtist(id: String) async throws -> ArtistDetail {
        return try await get("/artists/\(id)")
    }
}

// MARK: - Response Types

struct RatingResponse: Codable {
    let trackId: String
    let rating: Int?
    let excluded: Bool
    let favorite: Bool
    let notes: String?
}

struct AlbumDetail: Codable {
    let id: String
    let title: String
    let artistId: String?
    let artistName: String?
    let year: Int?
    let genre: String?
    let coverPath: String?
    let totalTracks: Int?
    let trackCount: Int?
    let tracks: [Track]
}

struct ArtistDetail: Codable {
    let id: String
    let name: String
    let sortName: String?
    let bio: String?
    let imagePath: String?
    let albumCount: Int?
    let trackCount: Int?
    let albums: [Album]
    let tracks: [Track]
}
