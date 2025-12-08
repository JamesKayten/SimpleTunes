import Foundation

// MARK: - API Error

enum APIError: Error, LocalizedError {
    case invalidURL
    case requestFailed(Error)
    case invalidResponse(Int)
    case decodingFailed(Error)
    case serverError(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .requestFailed(let error): return "Request failed: \(error.localizedDescription)"
        case .invalidResponse(let code): return "Invalid response: \(code)"
        case .decodingFailed(let error): return "Decoding failed: \(error.localizedDescription)"
        case .serverError(let message): return message
        }
    }
}

// MARK: - API Service Core

actor APIService {
    static let shared = APIService()
    
    let baseURL = "http://127.0.0.1:8000"
    
    let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        d.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)
            
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatter.date(from: dateString) { return date }
            
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: dateString) { return date }
            
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date: \(dateString)")
        }
        return d
    }()
    
    let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }()
    
    // MARK: - Health
    
    func healthCheck() async throws -> Bool {
        struct Health: Decodable { let status: String }
        let health: Health = try await get("/")
        return health.status == "ok"
    }
    
    // MARK: - HTTP Methods
    
    func get<T: Decodable>(_ path: String) async throws -> T {
        guard let url = URL(string: baseURL + path) else { throw APIError.invalidURL }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            try validateResponse(response)
            return try decoder.decode(T.self, from: data)
        } catch let error as APIError { throw error }
        catch let error as DecodingError { throw APIError.decodingFailed(error) }
        catch { throw APIError.requestFailed(error) }
    }
    
    func post<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        return try await request(path, method: "POST", body: body)
    }
    
    func put<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        return try await request(path, method: "PUT", body: body)
    }
    
    func delete(_ path: String) async throws {
        guard let url = URL(string: baseURL + path) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        let (_, response) = try await URLSession.shared.data(for: request)
        try validateResponse(response)
    }
    
    private func request<T: Decodable>(_ path: String, method: String, body: [String: Any]) async throws -> T {
        guard let url = URL(string: baseURL + path) else { throw APIError.invalidURL }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !body.isEmpty { request.httpBody = try JSONSerialization.data(withJSONObject: body) }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            try validateResponse(response)
            return try decoder.decode(T.self, from: data)
        } catch let error as APIError { throw error }
        catch let error as DecodingError { throw APIError.decodingFailed(error) }
        catch { throw APIError.requestFailed(error) }
    }
    
    private func validateResponse(_ response: URLResponse) throws {
        guard let httpResponse = response as? HTTPURLResponse else { return }
        switch httpResponse.statusCode {
        case 200...299: return
        case 404: throw APIError.serverError("Not found")
        case 400...499: throw APIError.serverError("Client error: \(httpResponse.statusCode)")
        case 500...599: throw APIError.serverError("Server error: \(httpResponse.statusCode)")
        default: throw APIError.invalidResponse(httpResponse.statusCode)
        }
    }
}

struct EmptyResponse: Decodable {}
