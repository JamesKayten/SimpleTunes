import SwiftUI

struct ContentView: View {
    @EnvironmentObject var player: PlayerViewModel
    @State private var searchText = ""
    @State private var showingNewPlaylist = false
    @State private var newPlaylistName = ""
    @State private var showQueue = false
    
    var body: some View {
        HStack(spacing: 0) {
            NavigationSplitView {
                List {
                    Section("Library") {
                        NavigationLink(destination: TrackListView()) {
                            Label("All Tracks", systemImage: "music.note.list")
                            Spacer()
                            if let c = player.stats?.totalTracks { Text("\(c)").foregroundStyle(.secondary) }
                        }
                        NavigationLink(destination: AlbumsView()) {
                            Label("Albums", systemImage: "square.stack")
                            Spacer()
                            if let c = player.stats?.totalAlbums { Text("\(c)").foregroundStyle(.secondary) }
                        }
                        NavigationLink(destination: ArtistsView()) {
                            Label("Artists", systemImage: "person.2")
                            Spacer()
                            if let c = player.stats?.totalArtists { Text("\(c)").foregroundStyle(.secondary) }
                        }
                        NavigationLink(destination: GenresView()) { Label("Genres", systemImage: "guitars") }
                    }
                    
                    Section("Smart Lists") {
                        NavigationLink(destination: SmartListView(type: .recentlyAdded)) { Label("Recently Added", systemImage: "clock") }
                        NavigationLink(destination: SmartListView(type: .recentlyPlayed)) { Label("Recently Played", systemImage: "play.circle") }
                        NavigationLink(destination: SmartListView(type: .mostPlayed)) { Label("Most Played", systemImage: "chart.bar") }
                        NavigationLink(destination: SmartListView(type: .favorites)) { Label("Favorites", systemImage: "heart.fill") }
                    }
                    
                    Section("Playlists") {
                        ForEach(player.playlists) { playlist in
                            NavigationLink(destination: PlaylistView(playlist: playlist)) {
                                Label(playlist.name, systemImage: "music.note")
                                Spacer()
                                if let c = playlist.trackCount { Text("\(c)").foregroundStyle(.secondary) }
                            }
                        }
                        Button { showingNewPlaylist = true } label: { Label("New Playlist...", systemImage: "plus") }
                    }
                }
                .navigationTitle("SimpleTunes")
                .toolbar {
                    ToolbarItem(placement: .primaryAction) {
                        Button { player.scanLibrary() } label: { Image(systemName: "arrow.clockwise") }
                            .help("Scan Music Library")
                    }
                }
            } detail: {
                TrackListView()
            }
            
            if showQueue { QueuePanel(isVisible: $showQueue) }
        }
        .searchable(text: $searchText, prompt: "Search...")
        .onChange(of: searchText) { _, v in player.search(query: v) }
        .overlay(alignment: .bottom) { NowPlayingBar(showQueue: $showQueue).padding() }
        .task { await player.loadAll() }
        .alert("New Playlist", isPresented: $showingNewPlaylist) {
            TextField("Playlist Name", text: $newPlaylistName)
            Button("Cancel", role: .cancel) { newPlaylistName = "" }
            Button("Create") { Task { _ = try? await player.createPlaylist(name: newPlaylistName); newPlaylistName = "" } }
        }
        .background(KeyboardShortcuts())
    }
}

struct KeyboardShortcuts: View {
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        Color.clear
            .frame(width: 0, height: 0)
            .onAppear { NSEvent.addLocalMonitorForEvents(matching: .keyDown) { handleKeyEvent($0) } }
    }
    
    private func handleKeyEvent(_ event: NSEvent) -> NSEvent? {
        guard !event.modifierFlags.contains(.command) else { return event }
        
        switch event.keyCode {
        case 49: // Space
            player.togglePlayPause(); return nil
        case 123: // Left arrow
            if event.modifierFlags.contains(.option) { player.skipBackward() }
            else { player.seek(to: max(0, player.currentTime - 10)) }
            return nil
        case 124: // Right arrow
            if event.modifierFlags.contains(.option) { player.skipForward() }
            else { player.seek(to: min(player.duration, player.currentTime + 10)) }
            return nil
        case 126: // Up arrow
            player.setVolume(min(1, player.volume + 0.1)); return nil
        case 125: // Down arrow
            player.setVolume(max(0, player.volume - 0.1)); return nil
        default:
            return event
        }
    }
}
