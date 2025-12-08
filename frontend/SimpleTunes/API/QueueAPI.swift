import Foundation

// MARK: - Queue API

extension APIService {
    
    func getQueue() async throws -> QueueState {
        return try await get("/queue")
    }
    
    func clearQueue() async throws {
        try await delete("/queue")
    }
    
    func addTracksToQueue(trackIds: [String], clearExisting: Bool = false, sourceType: String? = nil, sourceId: String? = nil) async throws -> Int {
        var body: [String: Any] = ["track_ids": trackIds, "clear_existing": clearExisting]
        if let t = sourceType { body["source_type"] = t }
        if let i = sourceId { body["source_id"] = i }
        struct R: Decodable { let added: Int }
        let r: R = try await post("/queue/tracks", body: body)
        return r.added
    }
    
    func addAlbumToQueue(albumId: String, clear: Bool = false) async throws -> Int {
        struct R: Decodable { let added: Int }
        let r: R = try await post("/queue/album/\(albumId)?clear=\(clear)", body: [:])
        return r.added
    }
    
    func addPlaylistToQueue(playlistId: String, clear: Bool = false) async throws -> Int {
        struct R: Decodable { let added: Int }
        let r: R = try await post("/queue/playlist/\(playlistId)?clear=\(clear)", body: [:])
        return r.added
    }
    
    func addArtistToQueue(artistId: String, clear: Bool = false) async throws -> Int {
        struct R: Decodable { let added: Int }
        let r: R = try await post("/queue/artist/\(artistId)?clear=\(clear)", body: [:])
        return r.added
    }
    
    func playNext(trackId: String) async throws -> Int {
        struct R: Decodable { let position: Int }
        let r: R = try await post("/queue/play-next/\(trackId)", body: [:])
        return r.position
    }
    
    func addToQueue(trackId: String) async throws -> Int {
        struct R: Decodable { let position: Int }
        let r: R = try await post("/queue/add/\(trackId)", body: [:])
        return r.position
    }
    
    func removeFromQueue(itemId: String) async throws {
        try await delete("/queue/items/\(itemId)")
    }
    
    func moveQueueItem(itemId: String, newPosition: Int) async throws {
        let _: EmptyResponse = try await put("/queue/items/\(itemId)/move?new_position=\(newPosition)", body: [:])
    }
    
    func getCurrentTrack() async throws -> Track? {
        struct R: Decodable { let track: Track? }
        let r: R = try await get("/queue/current")
        return r.track
    }
    
    func nextTrack() async throws -> Track? {
        struct R: Decodable { let track: Track? }
        let r: R = try await post("/queue/next", body: [:])
        return r.track
    }
    
    func previousTrack() async throws -> Track? {
        struct R: Decodable { let track: Track? }
        let r: R = try await post("/queue/previous", body: [:])
        return r.track
    }
    
    func playAtIndex(_ index: Int) async throws -> Track? {
        struct R: Decodable { let track: Track? }
        let r: R = try await post("/queue/play/\(index)", body: [:])
        return r.track
    }
    
    func setShuffle(enabled: Bool) async throws -> QueueState {
        return try await put("/queue/shuffle?enabled=\(enabled)", body: [:])
    }
    
    func setRepeat(mode: RepeatMode) async throws -> QueueState {
        return try await put("/queue/repeat?mode=\(mode.rawValue)", body: [:])
    }
    
    func getUpcoming(limit: Int = 10) async throws -> [Track] {
        struct R: Decodable { let tracks: [Track] }
        let r: R = try await get("/queue/upcoming?limit=\(limit)")
        return r.tracks
    }
    
    func getQueueHistory(limit: Int = 10) async throws -> [Track] {
        struct R: Decodable { let tracks: [Track] }
        let r: R = try await get("/queue/history?limit=\(limit)")
        return r.tracks
    }
}
