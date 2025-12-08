import SwiftUI

enum SmartListType {
    case recentlyAdded, recentlyPlayed, mostPlayed, favorites
    
    var title: String {
        switch self {
        case .recentlyAdded: return "Recently Added"
        case .recentlyPlayed: return "Recently Played"
        case .mostPlayed: return "Most Played"
        case .favorites: return "Favorites"
        }
    }
}

struct SmartListView: View {
    let type: SmartListType
    @EnvironmentObject var player: PlayerViewModel
    @State private var tracks: [Track] = []
    
    var body: some View {
        List(tracks) { track in
            HStack {
                TrackRow(track: track)
                Spacer()
                if type == .mostPlayed, let count = track.playCount {
                    Text("\(count) plays").font(.caption).foregroundStyle(.secondary)
                }
            }
            .contentShape(Rectangle())
            .onTapGesture { player.play(track: track) }
        }
        .navigationTitle(type.title)
        .task { await loadTracks() }
    }
    
    private func loadTracks() async {
        do {
            switch type {
            case .recentlyAdded: tracks = try await APIService.shared.getRecentlyAdded()
            case .recentlyPlayed: tracks = try await APIService.shared.getRecentlyPlayed()
            case .mostPlayed: tracks = try await APIService.shared.getMostPlayed()
            case .favorites: tracks = try await APIService.shared.getFavorites()
            }
        } catch { print("Failed to load \(type.title): \(error)") }
    }
}
