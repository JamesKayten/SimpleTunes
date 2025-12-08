import SwiftUI

struct ArtistsView: View {
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        List(player.artists) { artist in
            NavigationLink(destination: ArtistDetailView(artist: artist)) {
                HStack {
                    Circle().fill(.secondary.opacity(0.2)).frame(width: 44, height: 44)
                        .overlay { Image(systemName: "person.fill").foregroundStyle(.secondary) }
                    VStack(alignment: .leading) {
                        Text(artist.name).fontWeight(.medium)
                        if let count = artist.albumCount {
                            Text("\(count) albums").font(.caption).foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle("Artists")
    }
}

struct ArtistDetailView: View {
    let artist: Artist
    @EnvironmentObject var player: PlayerViewModel
    
    var artistAlbums: [Album] { player.albums.filter { $0.artistId == artist.id } }
    var artistTracks: [Track] { player.tracks.filter { $0.artistId == artist.id } }
    
    var body: some View {
        List {
            VStack(spacing: 8) {
                Circle().fill(.secondary.opacity(0.2)).frame(width: 120, height: 120)
                    .overlay { Image(systemName: "person.fill").font(.largeTitle).foregroundStyle(.secondary) }
                Text(artist.name).font(.title2).fontWeight(.bold)
                Text("\(artistAlbums.count) albums • \(artistTracks.count) tracks")
                    .font(.caption).foregroundStyle(.secondary)
            }.frame(maxWidth: .infinity).padding()
            
            if !artistAlbums.isEmpty {
                Section("Albums") {
                    ForEach(artistAlbums) { album in
                        NavigationLink(destination: AlbumDetailView(album: album)) { Text(album.title) }
                    }
                }
            }
            
            Section("All Tracks") {
                ForEach(artistTracks) { track in
                    TrackRow(track: track).contentShape(Rectangle())
                        .onTapGesture { player.play(track: track) }
                }
            }
        }
        .navigationTitle(artist.name)
    }
}

struct GenresView: View {
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        List(player.genres, id: \.name) { genre in
            NavigationLink(destination: GenreTracksView(genre: genre.name)) {
                HStack {
                    Text(genre.name)
                    Spacer()
                    Text("\(genre.count)").foregroundStyle(.secondary)
                }
            }
        }
        .navigationTitle("Genres")
    }
}

struct GenreTracksView: View {
    let genre: String
    @EnvironmentObject var player: PlayerViewModel
    
    var genreTracks: [Track] { player.tracks.filter { $0.genre?.lowercased() == genre.lowercased() } }
    
    var body: some View {
        List(genreTracks) { track in
            TrackRow(track: track).contentShape(Rectangle())
                .onTapGesture { player.play(track: track) }
        }
        .navigationTitle(genre)
    }
}
