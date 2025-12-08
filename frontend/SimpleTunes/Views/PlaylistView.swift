import SwiftUI

struct PlaylistView: View {
    let playlist: Playlist
    @EnvironmentObject var player: PlayerViewModel
    @State private var tracks: [Track] = []
    @State private var isLoading = true
    @State private var isEditing = false
    @State private var selectedTracks: Set<String> = []
    @State private var showDeleteConfirm = false
    
    var body: some View {
        VStack(spacing: 0) {
            if isEditing {
                EditingToolbar(
                    selectedCount: selectedTracks.count,
                    onDelete: { showDeleteConfirm = true },
                    onSelectAll: { selectedTracks = Set(tracks.map { $0.id }) },
                    onDeselectAll: { selectedTracks.removeAll() }
                )
            }
            
            List(selection: isEditing ? $selectedTracks : nil) {
                if isLoading {
                    ProgressView()
                } else if tracks.isEmpty {
                    Text("No tracks in this playlist").foregroundStyle(.secondary)
                } else {
                    ForEach(tracks) { track in
                        PlaylistTrackRow(track: track, isEditing: isEditing, isSelected: selectedTracks.contains(track.id),
                            onPlay: { playFrom(track: track) }, onRemove: { removeTrack(track) })
                            .tag(track.id)
                    }
                    .onMove(perform: isEditing ? moveTracks : nil)
                }
            }.listStyle(.plain)
        }
        .navigationTitle(playlist.name)
        .toolbar { playlistToolbar }
        .task { await loadTracks() }
        .confirmationDialog("Remove \(selectedTracks.count) track(s)?", isPresented: $showDeleteConfirm, titleVisibility: .visible) {
            Button("Remove", role: .destructive) { removeSelectedTracks() }
            Button("Cancel", role: .cancel) { }
        }
    }
    
    @ToolbarContentBuilder
    private var playlistToolbar: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button(isEditing ? "Done" : "Edit") {
                withAnimation { isEditing.toggle() }
                if !isEditing { selectedTracks.removeAll() }
            }
        }
        ToolbarItem(placement: .primaryAction) {
            Menu {
                Button("Play All") { player.playQueue(tracks: tracks) }
                Button("Shuffle") { player.shuffleEnabled = true; player.playQueue(tracks: tracks.shuffled()) }
                Divider()
                Button("Delete Playlist", role: .destructive) { player.deletePlaylist(playlist.id) }
            } label: { Image(systemName: "ellipsis.circle") }
        }
    }
    
    private func playFrom(track: Track) {
        player.playQueue(tracks: tracks, startIndex: tracks.firstIndex { $0.id == track.id } ?? 0)
    }
    
    private func loadTracks() async {
        isLoading = true; defer { isLoading = false }
        if let detail = try? await APIService.shared.getPlaylist(id: playlist.id) { tracks = detail.tracks }
    }
    
    private func removeTrack(_ track: Track) {
        Task {
            try? await APIService.shared.removeTrackFromPlaylist(playlistId: playlist.id, trackId: track.id)
            tracks.removeAll { $0.id == track.id }
        }
    }
    
    private func removeSelectedTracks() {
        Task {
            for id in selectedTracks { try? await APIService.shared.removeTrackFromPlaylist(playlistId: playlist.id, trackId: id) }
            tracks.removeAll { selectedTracks.contains($0.id) }
            selectedTracks.removeAll(); isEditing = false
        }
    }
    
    private func moveTracks(from source: IndexSet, to destination: Int) {
        tracks.move(fromOffsets: source, toOffset: destination)
        Task { try? await APIService.shared.reorderPlaylist(playlistId: playlist.id, trackIds: tracks.map { $0.id }) }
    }
}

struct PlaylistTrackRow: View {
    let track: Track, isEditing: Bool, isSelected: Bool
    let onPlay: () -> Void, onRemove: () -> Void
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        HStack(spacing: 12) {
            if isEditing {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundStyle(isSelected ? .accent : .secondary)
            }
            TrackRow(track: track)
            if isEditing {
                Button(role: .destructive, action: onRemove) {
                    Image(systemName: "minus.circle.fill").foregroundStyle(.red)
                }.buttonStyle(.plain)
            }
        }
        .contentShape(Rectangle())
        .onTapGesture { if !isEditing { onPlay() } }
        .contextMenu { TrackContextMenu(track: track) }
        .swipeActions(edge: .trailing, allowsFullSwipe: true) {
            Button(role: .destructive, action: onRemove) { Label("Remove", systemImage: "trash") }
        }
    }
}

struct EditingToolbar: View {
    let selectedCount: Int
    let onDelete: () -> Void, onSelectAll: () -> Void, onDeselectAll: () -> Void
    
    var body: some View {
        HStack {
            Text("\(selectedCount) selected").fontWeight(.medium)
            Spacer()
            Button("Select All", action: onSelectAll)
            Button("Deselect All", action: onDeselectAll)
            Button(role: .destructive, action: onDelete) { Label("Remove", systemImage: "trash") }.disabled(selectedCount == 0)
        }.padding(.horizontal).padding(.vertical, 8).background(.bar)
    }
}
