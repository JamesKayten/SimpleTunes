import SwiftUI
import AVFoundation

@MainActor
class PlayerViewModel: ObservableObject {
    // MARK: - Library State
    @Published var tracks: [Track] = []
    @Published var filteredTracks: [Track] = []
    @Published var albums: [Album] = []
    @Published var artists: [Artist] = []
    @Published var playlists: [Playlist] = []
    @Published var genres: [GenreCount] = []
    @Published var stats: LibraryStats?
    
    // MARK: - Playback State
    @Published var currentTrack: Track?
    @Published var isPlaying = false
    @Published var currentTime: Double = 0
    @Published var duration: Double = 0
    @Published var volume: Float = 0.7
    
    // MARK: - Queue State
    @Published var queue: [Track] = []
    @Published var queueIndex: Int = 0
    @Published var shuffleEnabled = false
    @Published var repeatMode: RepeatMode = .off
    
    // MARK: - UI State
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    // MARK: - Private
    private var player: AVAudioPlayer?
    private var timer: Timer?
    private let api = APIService.shared
    private var hasReportedPlay = false
    
    // MARK: - Loading
    
    func loadAll() async {
        isLoading = true
        defer { isLoading = false }
        
        async let t = try? api.getTracks(limit: 1000)
        async let a = try? api.getAlbums()
        async let ar = try? api.getArtists()
        async let p = try? api.getPlaylists()
        async let g = try? api.getGenres()
        async let s = try? api.getStats()
        
        tracks = (await t)?.tracks ?? []
        filteredTracks = tracks
        albums = (await a) ?? []
        artists = (await ar) ?? []
        playlists = (await p) ?? []
        genres = (await g) ?? []
        stats = await s
    }
    
    func scanLibrary(directory: String? = nil) {
        Task {
            isLoading = true
            defer { isLoading = false }
            _ = try? await api.scanLibrary(directory: directory ?? NSHomeDirectory() + "/Music")
            await loadAll()
        }
    }
    
    // MARK: - Search
    
    func search(query: String) {
        if query.isEmpty { filteredTracks = tracks; return }
        let q = query.lowercased()
        filteredTracks = tracks.filter {
            $0.title.lowercased().contains(q) ||
            $0.artist.lowercased().contains(q) ||
            $0.album.lowercased().contains(q)
        }
    }
    
    // MARK: - Playback
    
    func play(track: Track) {
        hasReportedPlay = false
        currentTrack = track
        
        do {
            player = try AVAudioPlayer(contentsOf: URL(fileURLWithPath: track.path))
            player?.volume = volume
            player?.play()
            isPlaying = true
            duration = player?.duration ?? track.duration ?? 0
            startTimer()
            Task { try? await api.updateNowPlaying(trackId: track.id) }
        } catch {
            errorMessage = "Playback failed: \(error.localizedDescription)"
        }
    }
    
    func togglePlayPause() {
        guard let player else { return }
        if player.isPlaying {
            player.pause(); isPlaying = false; timer?.invalidate()
        } else {
            player.play(); isPlaying = true; startTimer()
        }
    }
    
    func seek(to time: Double) { player?.currentTime = time; currentTime = time }
    func setVolume(_ value: Float) { volume = value; player?.volume = value }
    
    // MARK: - Queue
    
    func playQueue(tracks: [Track], startIndex: Int = 0) {
        queue = tracks; queueIndex = startIndex
        if let track = queue[safe: queueIndex] { play(track: track) }
    }
    
    func addToQueue(_ track: Track) {
        queue.append(track)
        Task { try? await api.addToQueue(trackId: track.id) }
    }
    
    func playNext(_ track: Track) {
        queue.insert(track, at: queue.isEmpty ? 0 : queueIndex + 1)
        Task { try? await api.playNext(trackId: track.id) }
    }
    
    func clearQueue() {
        queue.removeAll(); queueIndex = 0
        Task { try? await api.clearQueue() }
    }
    
    func removeFromQueue(at index: Int) {
        guard queue.indices.contains(index) else { return }
        queue.remove(at: index)
        if index < queueIndex { queueIndex -= 1 }
    }
    
    func skipForward() {
        reportPlayIfNeeded()
        if shuffleEnabled { playRandom(); return }
        if queueIndex + 1 < queue.count { queueIndex += 1; play(track: queue[queueIndex]) }
        else if repeatMode == .all && !queue.isEmpty { queueIndex = 0; play(track: queue[0]) }
    }
    
    func skipBackward() {
        if currentTime > 3 { seek(to: 0); return }
        if queueIndex > 0 { queueIndex -= 1; play(track: queue[queueIndex]) }
    }
    
    private func playRandom() {
        let source = queue.isEmpty ? filteredTracks : queue
        guard !source.isEmpty else { return }
        let idx = Int.random(in: 0..<source.count)
        if !queue.isEmpty { queueIndex = idx }
        play(track: source[idx])
    }
    
    func toggleShuffle() {
        shuffleEnabled.toggle()
        Task { try? await api.setShuffle(enabled: shuffleEnabled) }
    }
    
    func cycleRepeatMode() {
        repeatMode = repeatMode == .off ? .all : repeatMode == .all ? .one : .off
        Task { try? await api.setRepeat(mode: repeatMode) }
    }
    
    // MARK: - Ratings
    
    func setFavorite(_ track: Track, favorite: Bool) {
        Task { _ = try? await api.setFavorite(trackId: track.id, favorite: favorite) }
    }
    
    func setRating(_ track: Track, rating: Int) {
        Task { _ = try? await api.setRating(trackId: track.id, rating: rating) }
    }
    
    func addToPlaylist(_ track: Track, playlistId: String) {
        Task { try? await api.addTrackToPlaylist(playlistId: playlistId, trackId: track.id) }
    }
    
    func createPlaylist(name: String) async throws -> Playlist {
        let p = try await api.createPlaylist(name: name)
        await MainActor.run { Task { playlists = (try? await api.getPlaylists()) ?? playlists } }
        return p
    }
    
    func deletePlaylist(_ id: String) {
        Task { try? await api.deletePlaylist(id: id); playlists.removeAll { $0.id == id } }
    }
    
    // MARK: - Private
    
    private func startTimer() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self else { return }
                self.currentTime = self.player?.currentTime ?? 0
                self.checkPlayProgress()
                if let p = self.player, !p.isPlaying, self.isPlaying { self.handleTrackEnd() }
            }
        }
    }
    
    private func checkPlayProgress() {
        guard !hasReportedPlay, currentTime >= 30 || (duration > 0 && currentTime / duration >= 0.5) else { return }
        reportPlay()
    }
    
    private func reportPlay() {
        guard !hasReportedPlay, let track = currentTrack else { return }
        hasReportedPlay = true
        Task {
            _ = try? await api.recordPlay(trackId: track.id)
            try? await api.scrobbleTrack(trackId: track.id)
        }
    }
    
    private func reportPlayIfNeeded() { if currentTime >= 30 { reportPlay() } }
    
    private func handleTrackEnd() {
        reportPlayIfNeeded()
        if repeatMode == .one { seek(to: 0); player?.play() } else { skipForward() }
    }
}

extension Array { subscript(safe i: Int) -> Element? { indices.contains(i) ? self[i] : nil } }
