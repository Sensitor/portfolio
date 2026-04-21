public class VoieDeLaPriere extends Voie {
    public VoieDeLaPriere() {
        super("Voie de la priere");
        competences.add(new Competence("Benediction", 1));
        competences.add(new Competence("Destruction de morts-vivants", 2));
        competences.add(new Competence("Sanctuaire", 3));
        competences.add(new Competence("Intervention divine", 4));
    }
}
