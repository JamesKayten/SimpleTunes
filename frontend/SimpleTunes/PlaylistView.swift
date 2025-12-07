import SwiftUI

struct PlaylistView: View {
    let playlist: Playlist
    @EnvironmentObject var player: PlayerViewModel
    
    var playlistTracks: [Track] {
        playlist.trackIds.compactMap { id in
            player.tracks.first { $0.id == id }
        }
    }
    
    var body: some View {
        List(playlistTracks) { track in
            TrackRow(track: track)
                .contentShape(Rectangle())
                .onTapGesture { player.play(track: track) }
        }
        .listStyle(.plain)
        .navigationTitle(playlist.name)
    }
}
