import SwiftUI
import AVFoundation

@MainActor
class PlayerViewModel: ObservableObject {
    @Published var tracks: [Track] = []
    @Published var filteredTracks: [Track] = []
    @Published var playlists: [Playlist] = []
    @Published var currentTrack: Track?
    @Published var isPlaying = false
    @Published var currentTime: Double = 0
    @Published var duration: Double = 0
    
    private var player: AVAudioPlayer?
    private var timer: Timer?
    private let api = APIService.shared
    
    func loadLibrary() async {
        do {
            tracks = try await api.getLibrary()
            filteredTracks = tracks
        } catch {
            print("Load failed: \(error)")
        }
    }
    
    func scanLibrary() {
        Task {
            do {
                let result = try await api.scanLibrary(directory: NSHomeDirectory() + "/Music")
                print("Scanned: \(result.added) new, \(result.total) total")
                await loadLibrary()
            } catch {
                print("Scan failed: \(error)")
            }
        }
    }
    
    func search(query: String) {
        if query.isEmpty {
            filteredTracks = tracks
        } else {
            let q = query.lowercased()
            filteredTracks = tracks.filter {
                $0.title.lowercased().contains(q) ||
                $0.artist.lowercased().contains(q) ||
                $0.album.lowercased().contains(q)
            }
        }
    }
    
    func loadPlaylists() async {
        do {
            playlists = try await api.getPlaylists()
        } catch {
            print("Playlists failed: \(error)")
        }
    }
    
    func play(track: Track) {
        currentTrack = track
        do {
            player = try AVAudioPlayer(contentsOf: URL(fileURLWithPath: track.path))
            player?.play()
            isPlaying = true
            duration = player?.duration ?? track.duration
            startTimer()
        } catch {
            print("Playback failed: \(error)")
        }
    }
    
    func togglePlayPause() {
        guard let player else { return }
        if player.isPlaying {
            player.pause()
            isPlaying = false
            timer?.invalidate()
        } else {
            player.play()
            isPlaying = true
            startTimer()
        }
    }
    
    func seek(to time: Double) {
        player?.currentTime = time
        currentTime = time
    }
    
    func skipForward() {
        guard let current = currentTrack,
              let idx = filteredTracks.firstIndex(of: current),
              idx + 1 < filteredTracks.count else { return }
        play(track: filteredTracks[idx + 1])
    }
    
    func skipBackward() {
        if currentTime > 3 { seek(to: 0); return }
        guard let current = currentTrack,
              let idx = filteredTracks.firstIndex(of: current),
              idx > 0 else { return }
        play(track: filteredTracks[idx - 1])
    }
    
    private func startTimer() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor in
                self?.currentTime = self?.player?.currentTime ?? 0
                if let p = self?.player, !p.isPlaying, self?.isPlaying == true {
                    self?.skipForward()
                }
            }
        }
    }
}
