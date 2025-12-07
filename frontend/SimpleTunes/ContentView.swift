import SwiftUI

struct ContentView: View {
    @EnvironmentObject var player: PlayerViewModel
    @State private var searchText = ""
    
    var body: some View {
        NavigationSplitView {
            List {
                Section("Library") {
                    NavigationLink(destination: TrackListView()) {
                        Label("All Tracks", systemImage: "music.note.list")
                    }
                }
                Section("Playlists") {
                    ForEach(player.playlists) { playlist in
                        NavigationLink(destination: PlaylistView(playlist: playlist)) {
                            Label(playlist.name, systemImage: "music.note")
                        }
                    }
                }
            }
            .navigationTitle("SimpleTunes")
            .toolbar {
                Button(action: { player.scanLibrary() }) {
                    Image(systemName: "arrow.clockwise")
                }
            }
        } detail: {
            TrackListView()
        }
        .searchable(text: $searchText)
        .onChange(of: searchText) { _, newValue in
            player.search(query: newValue)
        }
        .overlay(alignment: .bottom) {
            NowPlayingBar().padding()
        }
        .task {
            await player.loadLibrary()
            await player.loadPlaylists()
        }
    }
}
